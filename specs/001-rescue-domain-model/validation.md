# Implementation validation

Validation executed from the repository root with CPython 3.14.10.

## Commands and results

| Command | Result |
| --- | --- |
| `python --version` | `Python 3.14.10` |
| `python -m unittest discover -s tests -p "test_*.py" -v` | Exit 0; 102 tests passed. This suite executes every acceptance scenario listed in [quickstart.md](quickstart.md). |
| `python -m rescue.demo` | Exit 0; `rescue demo: confirmed=10, pending=0, status=complete; comparisons=3 scenarios x 2 policies` |
| Quickstart callable API snippet | Printed `0 0 10` for confirmed, pending, and additional-needed seats. |
| `git diff --check` | Exit 0; no whitespace errors. Git printed a CRLF-to-LF normalization warning for `.specify/bridge-events.jsonl`. |

The focused suites for comparison, communication, resilience, architecture boundaries, and the demo also passed during implementation: 3, 15, 3, 4, and 3 tests respectively.

## Functional requirement evidence

| Requirement | Passing evidence |
| --- | --- |
| FR-001 | `test_values.py`, `test_mission.py`, and `test_market.py` validate input values, mission data, offers, and availability. |
| FR-002 | `test_mission.py`, `test_market.py`, `test_central.py`, and `test_concurrency.py` verify demand and shared-capacity invariants. |
| FR-003 | `test_mission.py` and `test_timing.py` cover full/partial acceptance, refusal, cancellation, and expiration. |
| FR-004 | `test_mission.py` and `test_central.py` verify derived progress and confirmed-only completion. |
| FR-005 | `test_central.py`, `test_concurrency.py`, and `test_communication.py` cover invalid, duplicate, conflicting, late, unknown, and reordered attempts. |
| FR-006 | `test_mission.py` and `test_central.py` verify one applied history entry per creation or terminal transition. |
| FR-007 | `test_central.py` and `test_communication.py` verify delivery diagnostics remain separate from applied history. |
| FR-008 | `test_market.py`, `test_central.py`, and `test_policies.py` cover immutable revisions, quote transfer, and retained revision basis. |
| FR-009 | `test_policies.py` and `test_central.py` verify candidate ranks, reasons, proposed quantities, and decision lookup. |
| FR-010 | `test_timing.py` and `test_communication.py` verify waiting, response elapsed time, and communication RTT separately. |
| FR-011 | `test_timing.py`, `test_central.py`, and `test_communication.py` verify optional deadlines and expiration-before-response behavior. |
| FR-012 | `test_experiment_models.py`, `test_experiments.py`, and `test_resilience.py` cover immutable baselines, scripts, profiles, horizons, seeds, and event budgets. |
| FR-013 | `test_comparison.py` and `test_demo.py` compare earliest-arrival and largest-capacity policies from the same scenario revision. |
| FR-014 | `test_communication.py` and `test_resilience.py` cover outbound/decision/return delays, loss, duplication, and reordering. |
| FR-015 | `test_results.py`, `test_experiments.py`, and `test_demo.py` verify run metrics and completed/incomplete results. |
| FR-016 | `test_experiments.py`, `test_comparison.py`, and `test_resilience.py` verify copied state, unchanged operational state, and horizon stopping. |
| FR-017 | `test_central.py` covers callable registration, coordination, progress, cancellation, expiration, and history. |
| FR-018 | `test_central.py` and `test_memory.py` verify state persists within one run and transaction snapshots are isolated. |
| FR-019 | `test_central.py` verifies one central coordinates distinct mission IDs and histories. |
| FR-020 | `test_mission.py` and `test_central.py` verify fixed mission demand and rejection of excess requests. |
| FR-021 | `test_central.py` verifies exact command replay and identity conflict on changed content. |
| FR-022 | `test_market.py` and `test_central.py` verify highest revision-number ordering and retained history. |
| FR-023 | `test_market.py` and `test_central.py` verify RFQ targets, held quotes, atomic transfer, and hold release. |
| FR-024 | `test_market.py`, `test_central.py`, and `test_concurrency.py` verify cross-mission holds and commitments, capacity shortfall, and allocation blocking. |
| FR-025 | The conceptual associations and `MissionOperations`/`ShipMarket` membership remain in the existing ER/UML references; `test_architecture.py` verifies code dependency direction, while `test_experiments.py` and `test_comparison.py` verify isolated market copies. No diagram semantics were changed. |

## Success criteria evidence

| Criterion | Passing evidence |
| --- | --- |
| SC-001 | `test_mission.py`, `test_market.py`, `test_central.py`, `test_concurrency.py`, and `test_communication.py`. |
| SC-002 | `test_mission.py`, `test_central.py`, and `test_policies.py`. |
| SC-003 | `test_experiments.py` and `test_resilience.py` repeat normalized seeded runs three times. |
| SC-004 | `test_demo.py` compares two policies for ordinary, partial/refusal, and delayed/lost/capacity-change scenarios. |
| SC-005 | `test_communication.py` verifies 10-second response elapsed time, 5-second RTT, and expiry at the receipt deadline. |
| SC-006 | `test_comparison.py` and `test_resilience.py` compare operational snapshots before and after isolated runs. |
| SC-007 | `test_central.py` and `test_memory.py` verify within-run state retention and independent contexts. |
| SC-008 | Existing ER/UML documentation retains the agreed conceptual memberships and relationships; `test_architecture.py`, `test_experiments.py`, and `test_comparison.py` verify implementation boundaries and isolated scenario markets. |
