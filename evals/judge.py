"""LLM-as-judge for groundedness: is every factual claim in the reply supported by the cited articles?

Only runs with --judge (costs API calls). Uses a separate model call with a strict rubric.
"""
from __future__ import annotations

import os

JUDGE_MODEL = os.environ.get("JUDGE_MODEL", os.environ.get("TRIAGE_MODEL", "claude-sonnet-4-5"))

RUBRIC = """You are grading a customer-support reply for groundedness.

Given help-center ARTICLES and a REPLY, decide whether every factual claim in the REPLY
(prices, limits, time windows, steps, policies) is directly supported by the ARTICLES.
Generic courtesy ("thanks for reaching out", "a specialist will follow up") is not a claim.

Call the grade tool with grounded=true only if there are no unsupported claims.
List each unsupported claim in `unsupported`."""

GRADE_TOOL = {
    "name": "grade",
    "description": "Record the groundedness verdict.",
    "input_schema": {
        "type": "object",
        "properties": {
            "grounded": {"type": "boolean"},
            "unsupported": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["grounded", "unsupported"],
    },
}


class GroundednessJudge:
    def __init__(self, kb, model: str = JUDGE_MODEL):
        import anthropic

        self.client = anthropic.Anthropic()
        self.kb = kb
        self.model = model

    def __call__(self, ticket, result) -> dict | None:
        if ticket.should_escalate or not result.reply_draft.strip():
            return None  # escalation replies are holding messages; nothing to ground
        ids = [c for c in result.citations if c in self.kb] or result.retrieved[:2]
        arts = "\n\n".join(f"[{i}] {self.kb[i].title}\n{self.kb[i].body}" for i in ids)
        resp = self.client.messages.create(
            model=self.model, max_tokens=512, temperature=0, system=RUBRIC,
            tools=[GRADE_TOOL], tool_choice={"type": "tool", "name": "grade"},
            messages=[{"role": "user", "content": f"ARTICLES:\n{arts}\n\nREPLY:\n{result.reply_draft}"}],
        )
        block = next(b for b in resp.content if b.type == "tool_use")
        return dict(block.input)
