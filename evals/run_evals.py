"""Run the triage agent over the labeled ticket set, score it, write a report, gate on thresholds.

    python -m evals.run_evals --agent baseline              # offline, no API key
    python -m evals.run_evals --agent claude --judge        # full run with groundedness judge
    python -m evals.run_evals --agent claude --limit 20     # quick smoke test
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import tomllib
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from triage.agent import make_agent
from triage.schema import Ticket, TriageResult

from .scorers import SCORERS

ROOT = Path(__file__).resolve().parent.parent
TICKETS = ROOT / "data" / "tickets.jsonl"
THRESHOLDS = ROOT / "evals" / "thresholds.toml"
RESULTS_DIR = ROOT / "evals" / "results"


def load_tickets(path=TICKETS, limit=None, types=None) -> list[Ticket]:
    rows = [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    tickets = [Ticket(**r) for r in rows]
    if types:
        tickets = [t for t in tickets if t.type in types]
    return tickets[:limit] if limit else tickets


def rate(values):
    vals = [v for v in values if v is not None]
    return (sum(bool(v) for v in vals) / len(vals), len(vals)) if vals else (None, 0)


def score(tickets, results, kb_ids, judgments=None):
    per_ticket = []
    for t, r in zip(tickets, results):
        row = {name: fn(t, r, kb_ids) for name, (fn, _) in SCORERS.items()}
        if judgments is not None:
            j = judgments.get(t.id)
            row["groundedness_rate"] = None if j is None else bool(j["grounded"])
        per_ticket.append(row)

    metrics = {}
    names = list(per_ticket[0]) if per_ticket else []
    for name in names:
        value, n = rate(row[name] for row in per_ticket)
        metrics[name] = {"value": value, "n": n}

    by_type = defaultdict(dict)
    for ttype in sorted({t.type for t in tickets}):
        idx = [i for i, t in enumerate(tickets) if t.type == ttype]
        for name in ("routing_accuracy", "escalation_accuracy", "citation_hit_rate"):
            by_type[ttype][name] = rate(per_ticket[i][name] for i in idx)[0]
        by_type[ttype]["n"] = len(idx)
    return per_ticket, metrics, dict(by_type)


def gate(metrics, thresholds):
    checks = []
    for name, rule in thresholds.items():
        m = metrics.get(name)
        if not m or m["value"] is None:
            continue  # metric not run (e.g. judge disabled)
        v = m["value"]
        if "min" in rule:
            ok, target = v >= rule["min"], f">= {rule['min']:.0%}"
        else:
            ok, target = v <= rule["max"], f"<= {rule['max']:.0%}"
        checks.append({"metric": name, "value": v, "target": target, "pass": ok})
    return checks


def fmt(v):
    return "n/a" if v is None else f"{v:.1%}"


def write_report(path, meta, metrics, checks, by_type, tickets, results, per_ticket, judgments):
    lines = [
        f"# Eval report: {meta['agent']}",
        "",
        f"- Run: {meta['timestamp']}",
        f"- Tickets: {meta['n_tickets']}  |  Errors: {meta['errors']}",
        f"- Median latency: {meta['median_latency_s']}s  |  Tokens in/out: {meta['input_tokens']:,} / {meta['output_tokens']:,}",
        f"- **Overall: {'PASS' if meta['passed'] else 'FAIL'}**",
        "",
        "## Acceptance thresholds",
        "",
        "| Metric | Value | Target | Result |",
        "| --- | --- | --- | --- |",
    ]
    for c in checks:
        lines.append(f"| {c['metric']} | {fmt(c['value'])} | {c['target']} | {'pass' if c['pass'] else '**FAIL**'} |")
    lines += ["", "## All metrics", "", "| Metric | Value | Tickets scored |", "| --- | --- | --- |"]
    for name, m in metrics.items():
        lines.append(f"| {name} | {fmt(m['value'])} | {m['n']} |")
    lines += ["", "## By ticket type", "", "| Type | n | Routing | Escalation | Citation hit |", "| --- | --- | --- | --- | --- |"]
    for ttype, m in by_type.items():
        lines.append(f"| {ttype} | {m['n']} | {fmt(m['routing_accuracy'])} | {fmt(m['escalation_accuracy'])} | {fmt(m['citation_hit_rate'])} |")

    lines += ["", "## Failures", ""]
    shown = 0
    for t, r, row in zip(tickets, results, per_ticket):
        bad = [k for k, (_, hib) in SCORERS.items() if row.get(k) is not None and bool(row[k]) != hib]
        if row.get("groundedness_rate") is False:
            bad.append("groundedness")
        if not bad:
            continue
        shown += 1
        if shown > 40:
            continue
        lines.append(
            f"- **{t.id}** ({t.type}) failed {', '.join(bad)}: expected queue `{t.expected_queue}`, "
            f"escalate={t.should_escalate}; got `{r.queue}`, escalate={r.escalate}, cited {r.citations or '[]'}"
            + (f"; error: {r.error}" if r.error else "")
        )
        j = (judgments or {}).get(t.id)
        if j and not j["grounded"]:
            lines.append(f"  - unsupported claims: {'; '.join(j['unsupported'])}")
    if shown > 40:
        lines.append(f"- ...and {shown - 40} more (see the JSON results file)")
    if shown == 0:
        lines.append("None.")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--agent", default="baseline", choices=["baseline", "claude"])
    p.add_argument("--model", help="override TRIAGE_MODEL for the claude agent")
    p.add_argument("--limit", type=int)
    p.add_argument("--types", nargs="*", choices=["routine", "edge", "risky"])
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--judge", action="store_true", help="run the LLM groundedness judge")
    p.add_argument("--no-gate", action="store_true", help="always exit 0 (for baseline runs)")
    a = p.parse_args(argv)

    kw = {"model": a.model} if (a.agent == "claude" and a.model) else {}
    agent = make_agent(a.agent, **kw)
    tickets = load_tickets(limit=a.limit, types=a.types)
    kb_ids = set(agent.kb)

    print(f"Running {agent.name} on {len(tickets)} tickets...", file=sys.stderr)
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        results: list[TriageResult] = list(pool.map(agent.triage, tickets))

    judgments = None
    if a.judge:
        from .judge import GroundednessJudge
        judge = GroundednessJudge(agent.kb)
        with ThreadPoolExecutor(max_workers=a.workers) as pool:
            verdicts = list(pool.map(lambda tr: judge(*tr), zip(tickets, results)))
        judgments = {t.id: v for t, v in zip(tickets, verdicts) if v is not None}

    per_ticket, metrics, by_type = score(tickets, results, kb_ids, judgments)
    thresholds = tomllib.loads(THRESHOLDS.read_text())
    checks = gate(metrics, thresholds)
    lat = sorted(r.latency_s for r in results)
    meta = {
        "agent": agent.name,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "n_tickets": len(tickets),
        "errors": sum(1 for r in results if r.error),
        "median_latency_s": lat[len(lat) // 2] if lat else 0,
        "input_tokens": sum(r.input_tokens for r in results),
        "output_tokens": sum(r.output_tokens for r in results),
        "wall_time_s": round(time.perf_counter() - t0, 1),
        "passed": all(c["pass"] for c in checks),
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stem = f"{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-{a.agent}"
    (RESULTS_DIR / f"{stem}.json").write_text(json.dumps({
        "meta": meta, "metrics": metrics, "checks": checks, "by_type": by_type,
        "results": [{"ticket": t.id, **r.to_dict(), "scores": s,
                     "judgment": (judgments or {}).get(t.id)}
                    for t, r, s in zip(tickets, results, per_ticket)],
    }, indent=2), encoding="utf-8")
    report = RESULTS_DIR / f"{stem}.md"
    write_report(report, meta, metrics, checks, by_type, tickets, results, per_ticket, judgments)
    (RESULTS_DIR / f"latest-{a.agent}.md").write_text(report.read_text(encoding="utf-8"), encoding="utf-8")

    for c in checks:
        print(f"{'PASS' if c['pass'] else 'FAIL'}  {c['metric']:<28} {fmt(c['value']):>7}  target {c['target']}")
    print(f"\nReport: {report.relative_to(ROOT)}")
    return 0 if (meta["passed"] or a.no_gate) else 1


if __name__ == "__main__":
    sys.exit(main())
