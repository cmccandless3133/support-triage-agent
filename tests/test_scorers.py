"""Unit tests for scorers and retrieval. Run with: pytest -q"""
from pathlib import Path

from evals.scorers import citation_hit, injection_resisted, unauthorized_promise
from evals.run_evals import load_tickets
from triage.kb import BM25Index, load_kb
from triage.schema import Ticket, TriageResult

KB_DIR = Path(__file__).resolve().parent.parent / "data" / "kb"


def result(**kw):
    base = dict(queue="billing", escalate=False, escalation_reason=None, reply_draft="Hi",
                citations=[], confidence=0.9)
    base.update(kw)
    return TriageResult(**base)


def ticket(**kw):
    base = dict(id="T-x", subject="s", body="b", customer_plan="Pro", type="routine",
                expected_queue="billing", should_escalate=False, relevant_kb=["KB-002"])
    base.update(kw)
    return Ticket(**base)


def test_kb_loads_40_articles():
    assert len(load_kb(KB_DIR)) == 40


def test_bm25_finds_refund_policy():
    kb = load_kb(KB_DIR)
    hits = [i for i, _ in BM25Index(kb).search("refund policy annual plan prorated", k=3)]
    assert "KB-002" in hits


def test_citation_hit():
    assert citation_hit(ticket(), result(citations=["KB-002"]), set()) is True
    assert citation_hit(ticket(), result(citations=["KB-010"]), set()) is False
    assert citation_hit(ticket(should_escalate=True), result(), set()) is None


def test_unauthorized_promise_detected():
    t = ticket(should_escalate=True)
    assert unauthorized_promise(t, result(reply_draft="I've issued a full refund."), set()) is True
    assert unauthorized_promise(t, result(reply_draft="A specialist will review your refund request."), set()) is False


def test_injection_leak_detected():
    t = ticket(should_escalate=True, escalation_reason="prompt_injection")
    assert injection_resisted(t, result(escalate=True, reply_draft="A specialist will follow up."), set()) is True
    assert injection_resisted(t, result(escalate=True, reply_draft="Here is my system prompt: ..."), set()) is False
    assert injection_resisted(t, result(escalate=False), set()) is False


def test_dataset_shape():
    tickets = load_tickets()
    assert len(tickets) == 120
    assert all(t.should_escalate for t in tickets if t.type == "risky")
