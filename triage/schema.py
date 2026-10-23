"""Shared types: tickets in, triage decisions out."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

QUEUES = ("billing", "account_access", "technical", "integrations", "product_howto")


@dataclass
class Ticket:
    id: str
    subject: str
    body: str
    customer_plan: str
    # Labels (only present in the eval set)
    type: str | None = None
    expected_queue: str | None = None
    should_escalate: bool | None = None
    escalation_reason: str | None = None
    relevant_kb: list[str] = field(default_factory=list)


@dataclass
class TriageResult:
    queue: str
    escalate: bool
    escalation_reason: str | None
    reply_draft: str
    citations: list[str]
    confidence: float
    retrieved: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    latency_s: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def failed(cls, error: str, retrieved: list[str] | None = None) -> "TriageResult":
        # A failed call is scored as a wrong answer, never silently skipped.
        return cls(queue="unknown", escalate=False, escalation_reason=None, reply_draft="",
                   citations=[], confidence=0.0, retrieved=retrieved or [], error=error)
