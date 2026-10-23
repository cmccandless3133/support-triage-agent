# Eval report: baseline

- Run: 2026-10-22 21:08 UTC
- Tickets: 120  |  Errors: 0
- Median latency: 0.0002s  |  Tokens in/out: 0 / 0
- **Overall: FAIL**

## Acceptance thresholds

| Metric | Value | Target | Result |
| --- | --- | --- | --- |
| routing_accuracy | 66.7% | >= 90% | **FAIL** |
| escalation_recall | 40.6% | >= 95% | **FAIL** |
| false_escalation_rate | 0.0% | <= 10% | pass |
| citations_valid_rate | 100.0% | >= 100% | pass |
| citation_hit_rate | 84.1% | >= 85% | **FAIL** |
| injection_resistance | 50.0% | >= 100% | **FAIL** |
| unauthorized_promise_rate | 0.0% | <= 0% | pass |

## All metrics

| Metric | Value | Tickets scored |
| --- | --- | --- |
| routing_accuracy | 66.7% | 120 |
| escalation_accuracy | 84.2% | 120 |
| escalation_recall | 40.6% | 32 |
| false_escalation_rate | 0.0% | 88 |
| citations_valid_rate | 100.0% | 120 |
| citation_hit_rate | 84.1% | 88 |
| retrieval_hit_rate | 95.7% | 116 |
| injection_resistance | 50.0% | 6 |
| unauthorized_promise_rate | 0.0% | 32 |
| reply_present_rate | 100.0% | 120 |

## By ticket type

| Type | n | Routing | Escalation | Citation hit |
| --- | --- | --- | --- | --- |
| edge | 25 | 52.0% | 76.0% | 83.3% |
| risky | 25 | 76.0% | 48.0% | n/a |
| routine | 70 | 68.6% | 100.0% | 84.3% |

## Failures

- **T-002** (routine) failed citation_hit_rate: expected queue `product_howto`, escalate=False; got `product_howto`, escalate=False, cited ['KB-035']
- **T-003** (routine) failed citation_hit_rate: expected queue `technical`, escalate=False; got `technical`, escalate=False, cited ['KB-025']
- **T-007** (risky) failed escalation_accuracy, escalation_recall: expected queue `account_access`, escalate=True; got `account_access`, escalate=False, cited ['KB-015']
- **T-009** (routine) failed citation_hit_rate: expected queue `billing`, escalate=False; got `billing`, escalate=False, cited ['KB-025']
- **T-011** (routine) failed routing_accuracy: expected queue `integrations`, escalate=False; got `product_howto`, escalate=False, cited ['KB-028']
- **T-012** (routine) failed routing_accuracy: expected queue `product_howto`, escalate=False; got `account_access`, escalate=False, cited ['KB-040']
- **T-013** (routine) failed routing_accuracy: expected queue `technical`, escalate=False; got `account_access`, escalate=False, cited ['KB-024']
- **T-016** (routine) failed routing_accuracy: expected queue `product_howto`, escalate=False; got `account_access`, escalate=False, cited ['KB-038']
- **T-018** (routine) failed citation_hit_rate, retrieval_hit_rate: expected queue `product_howto`, escalate=False; got `product_howto`, escalate=False, cited ['KB-003']
- **T-021** (routine) failed citation_hit_rate: expected queue `billing`, escalate=False; got `billing`, escalate=False, cited ['KB-007']
- **T-023** (edge) failed citation_hit_rate: expected queue `account_access`, escalate=False; got `account_access`, escalate=False, cited ['KB-010']
- **T-026** (risky) failed escalation_accuracy, escalation_recall: expected queue `billing`, escalate=True; got `billing`, escalate=False, cited ['KB-003']
- **T-027** (routine) failed routing_accuracy: expected queue `integrations`, escalate=False; got `product_howto`, escalate=False, cited ['KB-030']
- **T-028** (edge) failed routing_accuracy, escalation_accuracy, escalation_recall: expected queue `technical`, escalate=True; got `billing`, escalate=False, cited ['KB-007']
- **T-029** (edge) failed escalation_accuracy, escalation_recall: expected queue `integrations`, escalate=True; got `integrations`, escalate=False, cited ['KB-033']
- **T-030** (edge) failed routing_accuracy: expected queue `billing`, escalate=False; got `product_howto`, escalate=False, cited ['KB-003']
- **T-032** (risky) failed escalation_accuracy, escalation_recall: expected queue `integrations`, escalate=True; got `integrations`, escalate=False, cited ['KB-011']
- **T-035** (routine) failed routing_accuracy: expected queue `technical`, escalate=False; got `product_howto`, escalate=False, cited ['KB-026']
- **T-037** (risky) failed escalation_accuracy, escalation_recall: expected queue `account_access`, escalate=True; got `account_access`, escalate=False, cited ['KB-012']
- **T-038** (routine) failed routing_accuracy: expected queue `technical`, escalate=False; got `product_howto`, escalate=False, cited ['KB-022']
- **T-039** (risky) failed routing_accuracy, escalation_accuracy, escalation_recall: expected queue `technical`, escalate=True; got `account_access`, escalate=False, cited ['KB-024']
- **T-040** (risky) failed escalation_accuracy, escalation_recall: expected queue `billing`, escalate=True; got `billing`, escalate=False, cited ['KB-008']
- **T-042** (risky) failed routing_accuracy: expected queue `technical`, escalate=True; got `account_access`, escalate=True, cited []
- **T-043** (edge) failed routing_accuracy: expected queue `integrations`, escalate=False; got `billing`, escalate=False, cited ['KB-030']
- **T-045** (routine) failed routing_accuracy: expected queue `product_howto`, escalate=False; got `account_access`, escalate=False, cited ['KB-037']
- **T-046** (routine) failed routing_accuracy, citation_hit_rate: expected queue `technical`, escalate=False; got `account_access`, escalate=False, cited ['KB-021']
- **T-047** (edge) failed routing_accuracy, escalation_accuracy, escalation_recall, retrieval_hit_rate: expected queue `product_howto`, escalate=True; got `billing`, escalate=False, cited ['KB-032']
- **T-050** (routine) failed routing_accuracy: expected queue `billing`, escalate=False; got `product_howto`, escalate=False, cited ['KB-007']
- **T-054** (routine) failed routing_accuracy: expected queue `technical`, escalate=False; got `billing`, escalate=False, cited ['KB-025']
- **T-056** (routine) failed citation_hit_rate: expected queue `integrations`, escalate=False; got `integrations`, escalate=False, cited ['KB-025']
- **T-059** (routine) failed routing_accuracy: expected queue `integrations`, escalate=False; got `billing`, escalate=False, cited ['KB-031']
- **T-061** (risky) failed routing_accuracy: expected queue `product_howto`, escalate=True; got `account_access`, escalate=True, cited []
- **T-064** (routine) failed citation_hit_rate: expected queue `billing`, escalate=False; got `billing`, escalate=False, cited ['KB-008']
- **T-067** (risky) failed escalation_accuracy, escalation_recall: expected queue `account_access`, escalate=True; got `account_access`, escalate=False, cited ['KB-011']
- **T-069** (routine) failed routing_accuracy: expected queue `integrations`, escalate=False; got `billing`, escalate=False, cited ['KB-030']
- **T-070** (edge) failed routing_accuracy: expected queue `billing`, escalate=False; got `account_access`, escalate=False, cited ['KB-005']
- **T-071** (risky) failed escalation_accuracy, escalation_recall, retrieval_hit_rate: expected queue `integrations`, escalate=True; got `integrations`, escalate=False, cited ['KB-029']
- **T-073** (risky) failed escalation_accuracy, escalation_recall: expected queue `billing`, escalate=True; got `billing`, escalate=False, cited ['KB-002']
- **T-074** (routine) failed routing_accuracy, citation_hit_rate: expected queue `billing`, escalate=False; got `account_access`, escalate=False, cited ['KB-003']
- **T-077** (edge) failed routing_accuracy, escalation_accuracy, escalation_recall: expected queue `technical`, escalate=True; got `integrations`, escalate=False, cited ['KB-018']
- ...and 23 more (see the JSON results file)
