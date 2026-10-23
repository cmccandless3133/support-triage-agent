"""Triage agents: an LLM agent (Claude) and an offline keyword baseline."""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

from .kb import BM25Index, load_kb
from .prompts import SYSTEM_PROMPT, TRIAGE_TOOL, build_user_message
from .schema import QUEUES, Ticket, TriageResult

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_KB = ROOT / "data" / "kb"
# Model ids change over time; set TRIAGE_MODEL to the current one you want to test.
DEFAULT_MODEL = os.environ.get("TRIAGE_MODEL", "claude-sonnet-4-5")


class BaseAgent:
    name = "base"

    def __init__(self, kb_dir: str | Path = DEFAULT_KB, top_k: int = 4):
        self.kb = load_kb(kb_dir)
        self.index = BM25Index(self.kb)
        self.top_k = top_k

    def retrieve(self, ticket: Ticket):
        hits = self.index.search(f"{ticket.subject} {ticket.body}", k=self.top_k)
        return [self.kb[i] for i, _ in hits]

    def triage(self, ticket: Ticket) -> TriageResult:  # pragma: no cover - interface
        raise NotImplementedError


class ClaudeAgent(BaseAgent):
    """Retrieval + Claude tool call that forces a structured decision."""

    name = "claude"

    def __init__(self, model: str = DEFAULT_MODEL, max_retries: int = 3, **kw):
        super().__init__(**kw)
        import anthropic  # imported lazily so the offline baseline needs no SDK

        self.client = anthropic.Anthropic()
        self.model = model
        self.max_retries = max_retries
        self.name = f"claude:{model}"

    def triage(self, ticket: Ticket) -> TriageResult:
        articles = self.retrieve(ticket)
        retrieved = [a.id for a in articles]
        start = time.perf_counter()
        last_err = None
        for attempt in range(self.max_retries):
            try:
                resp = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    temperature=0,
                    system=SYSTEM_PROMPT,
                    tools=[TRIAGE_TOOL],
                    tool_choice={"type": "tool", "name": "submit_triage"},
                    messages=[{"role": "user", "content": build_user_message(ticket, articles)}],
                )
                block = next(b for b in resp.content if b.type == "tool_use")
                out = block.input
                return TriageResult(
                    queue=out.get("queue", "unknown"),
                    escalate=bool(out.get("escalate", False)),
                    escalation_reason=out.get("escalation_reason"),
                    reply_draft=out.get("reply_draft", ""),
                    citations=list(out.get("citations", [])),
                    confidence=float(out.get("confidence", 0.0)),
                    retrieved=retrieved,
                    input_tokens=resp.usage.input_tokens,
                    output_tokens=resp.usage.output_tokens,
                    latency_s=round(time.perf_counter() - start, 3),
                )
            except Exception as e:  # network, rate limit, malformed output
                last_err = f"{type(e).__name__}: {e}"
                time.sleep(2 ** attempt)
        return TriageResult.failed(last_err or "unknown error", retrieved)


class BaselineAgent(BaseAgent):
    """Keyword rules + top BM25 article. No API key needed.

    Exists so the harness runs anywhere (CI without secrets) and so the LLM agent
    has a naive score to beat in the write-up.
    """

    name = "baseline"
    QUEUE_WORDS = {
        "billing": "refund invoice charge charged billing plan price payment vat card receipt discount upgrade downgrade",
        "account_access": "password login log 2fa two-factor locked sso owner email account delete deletion seat",
        "technical": "error bug slow down outage loading browser captcha spam upload broken crash status",
        "integrations": "zapier slack sheets stripe mailchimp webhook api integration sync",
        "product_howto": "how logic embed domain theme badge question template conditional notification",
    }
    ESCALATE_RE = re.compile(
        r"lawyer|attorney|legal|sue|lawsuit|chargeback|dispute|gdpr|erase|erasure|breach|hacked|"
        r"ignore (all|your|previous)|system prompt|developer mode|hipaa|idiot|useless",
        re.I,
    )

    def triage(self, ticket: Ticket) -> TriageResult:
        start = time.perf_counter()
        articles = self.retrieve(ticket)
        text = f"{ticket.subject} {ticket.body}".lower()
        scores = {q: sum(text.count(w) for w in words.split()) for q, words in self.QUEUE_WORDS.items()}
        queue = max(scores, key=scores.get) if any(scores.values()) else (
            articles[0].category if articles else "technical")
        if queue not in QUEUES:
            queue = "technical"
        escalate = bool(self.ESCALATE_RE.search(text))
        top = articles[0] if articles else None
        if escalate or not top:
            reply = "Thanks for reaching out. A specialist will review this and follow up shortly."
        else:
            first_para = next((p for p in top.body.split("\n\n") if p and not p.startswith("#")), "")
            reply = f'Thanks for reaching out! This article should help: "{top.title}". {first_para}'.strip()
        return TriageResult(
            queue=queue, escalate=escalate,
            escalation_reason="keyword_match" if escalate else None,
            reply_draft=reply, citations=[top.id] if top and not escalate else [],
            confidence=0.5, retrieved=[a.id for a in articles],
            latency_s=round(time.perf_counter() - start, 4),
        )


def make_agent(kind: str, **kw) -> BaseAgent:
    if kind == "baseline":
        return BaselineAgent(**kw)
    if kind == "claude":
        return ClaudeAgent(**kw)
    raise ValueError(f"unknown agent: {kind}")
