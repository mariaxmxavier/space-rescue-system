# Implementation Plan: Clear and Ordered Communication

**Branch**: `007-communication-conformance` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/007-communication-conformance/spec.md`

## Summary

This feature turns `rescue/communication/` into a pure domain package of nested folders, one class or rule per file. It owns three B3-derived algorithms:

1. **Delivery classification**: the decision precedence now inside `RescueCentral.record_response`, extracted unchanged.
2. **Session sequencing and recovery** (B3 Binary EntryPoint):
   - ship-to-central responses use an idempotent inbound flow with `NotApplied` gap notices;
   - central-to-ship decision reports use a recoverable outbound flow.
3. **Per-mission decision order** (B3 matching engine, time half of price/time priority): every decision report carries the mission's existing `mission_sequence`.

`record_response` becomes a thin use case that gathers facts, calls the rules and publishes everything in one transaction. Unsequenced calls use a default local session, so the existing tests and the demo do not change. Every part carries a What / When called / Why / Diagram docstring, and the Communication UML and ER are brought in line with the code. Architecture tests and import contracts enforce the layout.

Execution: superpowers subagent-driven development in gated waves. `[P]` tasks inside a wave run as parallel subagents, each owning disjoint files (research P12).

## Technical Context

**Language/Version**: Python 3.14.10 (`.python-version`), uv 0.13.8

**Primary Dependencies**: standard library only inside `rescue/communication/` (`dataclasses`, `decimal`, `enum.StrEnum`). Dev tools are already pinned in `pyproject.toml`: ruff 0.17.5, pytest 9.2.0, pytest-cov 7.1.0, coverage 7.17.3, import-linter 2.16. Diagrams use Mermaid CLI 11.17.0 (`mmdc`). No new dependency.

**Storage**: in memory. `RunState.session_index` holds a tuple of immutable `CommunicationSession` values, published by `MemoryTransactionStore.transact` (research P4).

**Testing**: pytest.
- `tests/unit/communication/<topic>/` for pure rules, with no fakes and no I/O.
- `tests/integration/application/communication/` for wired behaviour through `new_run`.
- `tests/architecture/communication_layout/` for structure.
- `tests/e2e/demo` stays unchanged.

**Target Platform**: any platform running CPython 3.14

**Project Type**: library package inside one Python project (simulation driven by method calls)

**Performance Goals**: no new target. A recovery returns at most 1000 reports, and classification is constant work per delivery.

**Constraints**:
- Unsequenced calls and the demo keep their results.
- `rescue.communication.models` keeps exporting `CommunicationMessage` and `MessageDelivery`.
- Communication imports only `rescue.values` and the standard library.
- 100% line and branch coverage for `rescue/communication`.
- No commits unless the maintainer asks (AGENTS.md section 8).

**Scale/Scope**:
- 1 source file (110 lines) becomes about 25 small files.
- `record_response` (about 180 lines) shrinks to fact gathering and publication.
- 3 application files, 2 experiments files, 4 diagram pairs and 1 README section change.

All Technical Context items are resolved; research.md P1-P12 records each planning decision.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How this plan keeps it | Status |
|-----------|------------------------|--------|
| I. Safe Seat Accounting | Mission rules and capacity checks are untouched. Sequencing never replaces the transaction. Replay and duplicate fixtures assert zero seat changes (SC-003). | PASS |
| II. Final Request Outcomes | The precedence table (research P6) keeps today's order after the session step. The race fixtures (SC-006) assert that closed requests stay closed. | PASS |
| III. Reliable Operations | Repeated, delayed and out-of-order messages each have a named outcome. One transaction publishes the session, delivery, mission and report changes, or none of them. Concurrency is tested across sessions and missions. | PASS |
| IV. Simple Design | No new mechanism for mission order: the existing `mission_sequence` is reused (P1). Sessions are implicit (P5). New application methods stay on `RescueCentral` until 008 (P11). The file split is an explicit spec requirement (FR-008). | PASS |
| V. Evidence and Explainability | Unit tests per rule, integration tests per story, architecture tests and the unchanged demo. The README gains the ordering and concurrency explanation. | PASS |
| Workflow: parallel writers own disjoint files | Every `[P]` task names its files, and no two `[P]` tasks in a wave share one (Delivery strategy below). | PASS |
| Exact versions | No new dependency | PASS |

Post-design re-check (after Phase 1): PASS. The design adds no unrequested abstraction. One recorded deviation, parallel implementers, is in research P12 at the maintainer's request; it is not a constitution violation. Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/007-communication-conformance/
├── spec.md
├── plan.md                  # this file
├── research.md              # market research + planning decisions P1-P12
├── data-model.md            # Phase 1: entities, fields, rules, diagram deltas
├── design-diagrams.md       # Phase 1: components, sequence, state machines
├── quickstart.md            # Phase 1: how to verify
├── contracts/
│   ├── maintainability.md   # files, docstrings, diagrams, verification (from specify)
│   ├── public-imports.md    # names each import path must export
│   ├── import-contracts.md  # import-linter contracts and coverage gate
│   └── application-api.md   # RescueCentral commands, results and reasons
├── checklists/requirements.md
└── tasks.md                 # /speckit-tasks (not created here)
```

### Source Code (repository root)

```text
rescue/communication/
├── __init__.py                      overview docstring (contract questions 1-6), no code
├── models/
│   ├── __init__.py                  re-exports every public model name
│   ├── _validation.py               kind and payload helpers (moved unchanged)
│   ├── vocabulary/
│   │   ├── delivery_disposition.py  DeliveryDisposition
│   │   ├── delivery_reason.py       DeliveryReason
│   │   ├── flow_direction.py        FlowDirection
│   │   └── recovery_rejection.py    RecoveryRejection
│   ├── messages/
│   │   └── communication_message.py CommunicationMessage (moved unchanged)
│   ├── deliveries/
│   │   ├── message_delivery.py      MessageDelivery (+ optional envelope)
│   │   ├── delivery_facts.py        DeliveryFacts
│   │   └── delivery_decision.py     DeliveryDecision
│   ├── sessions/
│   │   ├── session_envelope.py      SessionEnvelope
│   │   ├── communication_session.py CommunicationSession
│   │   └── not_applied.py           NotApplied
│   └── recovery/
│       ├── decision_report.py       DecisionReport
│       ├── recovery_request.py      RecoveryRequest
│       ├── sequence_control.py      SequenceControl
│       └── report_cursor.py         ReportCursor
└── rules/
    ├── __init__.py                  re-exports every public rule
    ├── classify_delivery.py         facts → DeliveryDecision (P6 rows 1-2, 4-11)
    ├── accept_inbound.py            session + envelope → session, NotApplied?, verdict (P6 row 3)
    ├── issue_report.py              session + decision → session, DecisionReport
    ├── recover_reports.py           session + RecoveryRequest → reports + SequenceControl | rejection
    ├── synchronise_inbound.py       session + SequenceControl → session, NotApplied? | rejection
    └── receive_report.py            ReportCursor + report → cursor, deliverable reports, gap?

rescue/application/
├── contracts.py                     RecordResponse.envelope; RecoverReports; SynchroniseInbound; ErrorReason values
├── state.py                         RunState.session_index
└── central.py                       record_response (thin); recover_reports; synchronise_inbound; get_session

rescue/experiments/
├── models.py                        RunBaseline.session_index, RunSnapshot.session_index
└── runner.py                        copy session_index on install and snapshot

tests/unit/communication/
├── models/<one test file per model>
└── rules/<one test file per rule>
tests/integration/application/communication/
├── test_communication.py            existing, unchanged
├── test_sessions.py                 Story 2.1-2.3, 2.5-2.7
├── test_recovery.py                 Story 2.4, 2.8
└── test_mission_order.py            Story 3
tests/integration/application/concurrency/test_session_concurrency.py   Story 2.7, 3.4
tests/integration/experiments/session_copy/test_session_copy.py                       FR-007, FR-014 copies
tests/architecture/communication_layout/
├── test_one_public_name_per_file.py
├── test_docstrings.py
└── test_diagrams_match_code.py

docs/architecture/diagrams/rescue-domain-model/
├── namespaces/Communication/class-diagram.{mmd,svg}
├── namespaces/Communication/entity-relationship-diagram.{mmd,svg}
├── class-diagrams/scenario-model.{mmd,svg}
└── entity-relationship-diagrams/scenario-model-er.{mmd,svg}
README.md                            communication ordering + concurrency paragraph
```

**Structure Decision**: This follows spec 004's mission layout. Under cosmic-python, `models/` and `rules/` are both the models layer: pure, no I/O, no orchestration. `rules/` imports `models/`, never the reverse, which import-linter enforces. Application orchestration stays in `rescue/application/central.py`, the services layer, until 008 splits it. The store, the outer adapter, is unchanged. Clean Architecture: communication policy knows nothing of the store, the lock or the mission aggregate. The application turns mission facts into primitives at the boundary (research P10).

## Delivery strategy (subagent-driven, parallel)

Each wave ends with `make check-all` green before the next starts; the controller runs it. Within a wave, `[P]` tasks run as parallel subagents. Each owns only the files it lists, writes its test first (superpowers:test-driven-development), and does not commit. Each task gets a two-stage review: spec compliance, then quality.

| Wave | Tasks | Parallel | Owns |
|------|-------|----------|------|
| 0 | Bridge handoff points at 007 (after `/speckit-tasks`, by its hook) | no | bridge state |
| 1 | Foundation. Turn `models.py` into the `models/` package: move `CommunicationMessage`, `MessageDelivery` and `_validation.py` unchanged, re-export from `models/__init__.py`. Add the 4 vocabularies and their tests, the 2 import contracts, the Makefile `--fail-under=100`, and the architecture tests marked `xfail(strict=True)` until wave 4. | no | `rescue/communication/**` existing, `pyproject.toml`, `Makefile`, `tests/architecture/communication_layout/` |
| 2 | One subagent per new model: file + unit test. Adds `envelope` to `MessageDelivery`. Tests import the deep path; `__init__` is not touched. | **[P] ×10** | one model file + one test file each |
| 3 | One subagent per rule: file + unit test, covering every row of research P6 and P8 | **[P] ×6** | one rule file + one test file each |
| 4 | Integration of the package: `models/__init__` and `rules/__init__` exports, `xfail` removed, `rescue/communication/__init__.py` overview | no | the 3 `__init__.py`, architecture tests |
| 5 | Application: `contracts.py`, `state.py`, `central.py` (thin `record_response`, 3 new methods), existing integration suite green, demo identical | no | 3 application files |
| 6 | Experiments copy; 5 new integration test files; README; 4 diagram pairs (`.mmd` + `.svg`) and the diagram README note | **[P] ×11** | one file group each (list below) |
| 7 | Verify: `make check-all`, demo identical, communication coverage 100%, quickstart walk-through | no | none (read-only) |

Wave 6 file groups, one subagent each:
1. `rescue/experiments/models.py` + `runner.py`
2. `test_sessions.py`
3. `test_recovery.py`
4. `test_mission_order.py`
5. `test_session_concurrency.py`
6. `tests/integration/experiments/session_copy/test_session_copy.py`
7. `README.md`
8. Communication class pair
9. Communication ER pair
10. scenario-model class pair
11. scenario-model ER pair; this agent also adds the diagram README note.

Why waves 2 and 3 can run in parallel: every new file sits beside the moved code, and no package `__init__` changes until wave 4, so the suite stays green throughout. Wave 5 is serial because `central.py` is one shared file. Wave 6's test files test the wave 5 surface, which is frozen by then.

Model tiers follow the skill: cheap for single-file model and vocabulary tasks; standard for rules, application and tests; the most capable model for the final whole-branch review. Each brief carries:
- the FR it serves;
- its owned files;
- the docstring contract (contracts/maintainability.md);
- the precedence table, for rules;
- the "unsequenced results unchanged" rule;
- the gate command.

## Complexity Tracking

No violations.
