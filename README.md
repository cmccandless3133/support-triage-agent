# Support Triage Agent with an Eval Suite

An AI agent that reads customer support tickets, routes each one to the right queue, drafts a reply grounded in the help center, and hands risky tickets to a human. It ships with an **evaluation suite of 120 labeled tickets**, so every change is measured, not guessed at.

Built for **Larkspur Forms**, a fictional form-builder SaaS. All data is synthetic.

## Why this exists

Most support bots are demoed on five friendly questions. Real inboxes include refund demands outside policy, legal threats, people trying to get another customer's API keys, and messages that say "ignore your previous instructions." This project shows how to build the agent **and** how to prove it handles those cases.

## How it works

```
ticket ──► BM25 retrieval (top 4 of 40 help-center articles)
              │
              ▼
        Claude, forced tool call `submit_triage`
              │   queue · escalate · reason · reply · citations · confidence
              ▼
        structured decision ──► eval scorers ──► report + CI gate
```

- **Retrieval:** pure-Python BM25 over the help center (no vector database to run).
- **Agent:** one Claude call with a forced tool call, so output is always valid structured data. Ticket text is wrapped in `<ticket>` tags and treated as data, not instructions.
- **Baseline:** a keyword-rules agent that runs offline. It's the score to beat, and it lets CI run without an API key.

## The eval suite

`data/tickets.jsonl` has 120 labeled tickets:

| Type | Count | What it tests |
| --- | --- | --- |
| Routine | 70 | Answerable from the help center |
| Edge | 25 | Vague, multi-issue, angry, typos, partly covered |
| Risky | 25 | Refunds outside policy, legal threats, breaches, GDPR, chargebacks, abuse, 6 prompt injections |

Each ticket is labeled with its correct queue, whether it must escalate, why, and which articles answer it.

### Metrics and acceptance thresholds

| Metric | What it catches | Target |
| --- | --- | --- |
| Routing accuracy | Ticket sent to the wrong team | ≥ 90% |
| Escalation recall | Risky ticket answered by the bot instead of a human | ≥ 95% |
| False escalation rate | Bot dumps easy tickets on humans | ≤ 10% |
| Citations valid | Made-up article ids | 100% |
| Citation hit rate | Reply relies on the wrong article | ≥ 85% |
| Injection resistance | "Ignore your instructions" works, or secrets leak | 100% |
| Unauthorized promises | Reply promises a refund or deletion a human hasn't approved | 0% |
| Groundedness (LLM judge, optional) | Claims not supported by the cited articles | ≥ 85% |

Retrieval hit rate is reported separately, so you can tell retrieval failures from generation failures.

## Results

| Agent | Routing | Escalation recall | Injection resistance | Citation hit | Pass? |
| --- | --- | --- | --- | --- | --- |
| Keyword baseline | 66.7% | 40.6% | 50.0% | 84.1% | No |
| Claude agent (`[model]`) | [X]% | [X]% | [X]% | [X]% | [ ] |

*(Fill in the Claude row from `evals/results/latest-claude.md` after your first run.)*

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

make test        # unit tests for scorers and retrieval
make baseline    # offline eval, no API key needed

cp .env.example .env   # add your ANTHROPIC_API_KEY
make eval        # full eval with the Claude agent
make eval-judge  # plus the LLM groundedness judge
make smoke       # 20 tickets, a quick check while iterating
```

Triage one ticket:

```bash
python -m triage.cli --subject "Refund please" --body "I signed up 3 days ago and want my money back" --plan Starter
```

Reports land in `evals/results/` as Markdown (for humans) and JSON (every prediction and score).

## CI

`.github/workflows/evals.yml` runs the unit tests and the baseline on every push. If the `ANTHROPIC_API_KEY` repository secret is set, it also runs the Claude eval and **fails the build when any threshold is missed**. The report is uploaded as a build artifact.

## Project layout

```
triage/        agent, retrieval, prompts, CLI
evals/         scorers, LLM judge, runner, thresholds.toml
data/kb/       40 help-center articles (synthetic)
data/          tickets.jsonl, the labeled eval set
tests/         pytest unit tests
```

## What I'd do next for a real client

- Build the test set from 50–200 of their real (anonymized) tickets
- Add evals for tone and reply length, and track cost per ticket
- Run the eval nightly against live traffic samples to catch drift when models update

## License

MIT
