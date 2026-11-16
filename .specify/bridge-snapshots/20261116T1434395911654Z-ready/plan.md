# Rescue Domain Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build safe in-memory rescue coordination with explainable decisions and reproducible isolated experiments.

**Architecture:** Mission owns request transitions and mission invariants; B3Market owns inventory and quote rules. RescueCentral coordinates both through an application-owned atomic transaction port, with in-memory locking supplied by an outer adapter. Simulation reuses these rules in independent run contexts.

**Tech Stack:** CPython 3.14.10; standard library only; unittest.

**Spec:** [spec.md](spec.md), [constitution](../../.specify/memory/constitution.md).

**Branch:** actual Git branch `feature/rescue-domain-model`; Spec Kit resolved feature key `001-rescue-domain-model`. No branch was created by this planning command.
**Date:** 2026-11-16. **Status:** proposed design for review; spec remains draft.

## Global Constraints

- “Python is the project's chosen language; the original problem permits other languages.”
- “Dependencies MUST use exact versions.” Implementation chooses Python 3.14.10 and no third-party dependencies.
- “Mission owns its requests, their state transitions, and mission invariants.”
- “Keep a registered mission's people count fixed for its lifetime; reject attempts to change it after registration.”
- “Fleet-wide allocation optimization, flights, boarding, routes, and storm simulation remain excluded.”
- “No live external market feed, trading integration, HTTP service, or real timers are required.”
- Exactly one central per application run; state lasts only for that run. Quotes are holds, never confirmed transport.
- Parallel writers own disjoint paths. No commits, pushes or PRs without explicit user authorization; proposed task checkpoints do not authorize commits.

## Review Focus

1. Bool/fractional quantities and non-finite times must reject before state mutation (Task 1).
2. A failed quote transfer must retain its hold and create no request/history/index record (Task 5).
3. Capacity reduction below commitments must expose shortfall without revoking seats (Tasks 3 and 5).
4. Retry after quote expiry or request closure must return the original result; altered content must conflict (Task 5).
5. Equal-time deadlines and zero-delay repeated deliveries must terminate deterministically without extra confirmations (Task 6).

## Technical Context

**Language/Version:** CPython 3.14.10, exact runtime pin during Task 1.
**Primary Dependencies:** standard library; no third-party packages.
**Storage:** run-local immutable state snapshots behind one in-memory transaction adapter.
**Testing:** unittest unit, contract, integration and architecture-import tests.
**Target Platform:** Windows and Linux with the pinned interpreter; no server.
**Project Type:** Python callable library and reproducible command-line demonstration.
**Performance Goals:** no throughput/SLA specified; finite scripted scenarios terminate at horizon with no wall-clock sleeps. Prefer correctness and determinism; no invented benchmark gate.
**Constraints:** C+P<=D; shared ship inventory; terminal outcomes; exact retry identity; immutable history/revisions; experiment isolation.
**Scale/Scope:** one central and market per context, multiple ships/missions, two policies, three comparison scenarios. No multi-process shared state.

## Constitution Check

| Gate | Before research | After design | Evidence |
| --- | --- | --- | --- |
| I Safe accounting | Pass | Pass | Derived quantities, latest inventory validation, atomic transfer; capacity-shortfall exception explicit |
| II Final outcomes | Pass | Pass | Terminal transition table and deadline precedence |
| III Reliable operations | Pass | Pass | One store lock, staged publication, payload identity and disposition rules |
| IV Simple design | Pass | Pass | Standard library, inward dependencies, no remote infrastructure |
| V Evidence | Pass | Pass | Task tests and quickstart cover all stories, concurrency and demo |
| Scope/workflow | Pass | Pass | Exact runtime; documented choices; no implementation in planning pass |

No constitutional deviations. These are design gates, not claims that implementation tests passed. User review of draft requirements and proposed policies remains necessary before implementation.

## Phase 0: Research

Completed [research.md](research.md): runtime, architecture, consistency, identities, timing, quote expiry, direct requests and reproducibility. Read-only research corroborated single-transaction capacity safety, terminal quote ownership, immutable revisions and simulation isolation. Official Python documentation supports the selected standard-library mechanisms; no unresolved technical placeholders remain.

## Phase 1: Design

Completed [data-model.md](data-model.md), [callable contracts](contracts/callable-api.md) and [quickstart.md](quickstart.md). Existing [ER/UML views](../../docs/diagrams/rescue-domain-model/README.md) remain unchanged conceptual references. Their namespaces do not mandate deployment or package boundaries.

## Project Structure

Planning outputs live under `specs/001-rescue-domain-model/`: plan.md, research.md, data-model.md, contracts/callable-api.md, quickstart.md. `tasks.md` is reserved for speckit-tasks, which can derive executable tasks from the work breakdown below; it is not created by speckit-plan. This plan is the canonical implementation plan instead of a duplicate under docs/superpowers/plans.

Planned source files (all new; no Python implementation currently exists):

| Paths | Responsibility / owning task |
| --- | --- |
| `.python-version`, `pyproject.toml`, `rescue/__init__.py`, `rescue/values.py`, `rescue/application/contracts.py` | Runtime and shared DTO schema, Task 1 |
| `rescue/mission/{__init__,models,rules}.py` | Mission data, request history, transitions, progress, Task 2 |
| `rescue/market/{__init__,models,rules}.py` | Ships, revisions, RFQs, quote lifecycle and inventory, Task 3 |
| `rescue/mobilisation/{__init__,models,policies}.py` | Candidate snapshots, policy revisions, evaluations, Task 4 |
| `rescue/communication/{__init__,models}.py` | Logical messages and diagnostic deliveries, Task 1 |
| `rescue/application/{__init__,ports,state,central}.py`, `rescue/adapters/{__init__,memory}.py`, `rescue/bootstrap.py` | Atomic orchestration and composition, Task 5 |
| `rescue/experiments/{__init__,models,timeline,runner,results}.py`, `rescue/demo.py` | Isolated reproducible comparisons and demo, Task 6 |
| `tests/test_values.py`, `tests/test_contracts.py` | Shared input/DTO validation, Task 1 |
| `tests/test_mission.py`, `tests/test_market.py`, `tests/test_policies.py` | Disjoint pure rule suites, Tasks 2–4 respectively |
| `tests/test_central.py`, `tests/test_concurrency.py`, `tests/test_architecture.py` | Orchestration, atomicity and import boundaries, Task 5 |
| `tests/test_experiments.py`, `tests/test_demo.py`, `README.md` | Acceptance comparisons and usage, Task 6 |

Each owner creates package __init__.py only in its assigned directories. Task 1 creates the application package marker so later contracts import cleanly. If a downstream task discovers a contract change, stop dependent work and coordinate one owner; no parallel edits to shared contracts.

## Implementation work breakdown

`[P]` means eligible for parallel execution only after listed prerequisites complete and shared interfaces are frozen. Tasks 2, 3 and 4 may run together; all others are sequential. Each task uses contracts/callable-api.md and data-model.md, which define the shared names, signatures and expected values.

### Task 1: Freeze shared value and callable contracts

**Files:** Task 1 paths above. **Depends on:** design review.
**Consumes:** entity catalogue and callable contract. **Produces:** Instant, Id, TransitionContext, command dataclasses, Result[T], message/delivery types. DTO snapshot types belong to their capability model files; use deferred type imports to avoid runtime cycles.

- [ ] Write `test_reject_invalid_inputs` asserting True, 1.5 and 0 reject as positive seat quantities; '-1', 'NaN', 'Infinity' and float times reject; time '0' accepts; blank identity rejects. Write `test_dto_snapshot_immutable` asserting collection inputs cannot mutate a constructed DTO.
- [ ] Run `python -m unittest discover -s tests -p test_values.py -v`; expect failure because rescue.values does not exist.
- [ ] Implement value normalization and command schemas in assigned files with exact field names from the callable contract; pin Python to 3.14.10, no runtime dependencies. Define TransitionContext(event_id, at, reason, message_id=None).
- [ ] Run `python -m unittest discover -s tests -p 'test_*contracts.py' -v` and the values command; expect all cases pass. Ensure test_contracts.py covers every command's required fields and rejects unknown fields.
- [ ] Review the scoped diff; record verification. Commit checkpoint only if user explicitly authorizes it.

### Task 2 [P]: Mission accounting and history

**Files:** mission package and tests/test_mission.py. **Depends on:** Task 1.
**Consumes:** shared values and TransitionContext. **Produces:** Mission, SeatRequest, RequestHistoryEntry, MissionProgress and mission functions from the callable contract.

- [ ] Write `test_partial_closes_and_releases`: demand=10, request=6, accept=4 yields C=4,P=0,additional_needed=6 and exactly two history entries. Write full-accept/refuse/cancel/expire cases from the transition table; closed requests reject every further transition unchanged.
- [ ] Run `python -m unittest discover -s tests -p test_mission.py -v`; expect missing mission module failure.
- [ ] Implement immutable Mission values and pure rule functions; derived totals only, immutable demand, consecutive sequence and unique supplied event IDs. Public snapshots expose no internal mutable references.
- [ ] Add `test_pending_never_completes` (10 pending -> awaiting_responses), `test_overrequest_preserves_state`, `test_demand_immutable` and `test_terminal_partial_response_cannot_reopen`; rerun same command expecting all pass.
- [ ] Review scoped diff and record checks; commit only with authorization.

### Task 3 [P]: Shared market and quote lifecycle

**Files:** market package and tests/test_market.py. **Depends on:** Task 1.
**Consumes:** shared values; a structural commitment view (ship_id, requested_seats, confirmed_seats, outcome) so this task does not import an unfinished Mission implementation. Final usage accepts Mission values conforming to that view. **Produces:** market entities, ShipUsage and market functions from contract.

- [ ] Write `test_quote_transfer_counts_once`: total=6, held=4 -> transfer -> held=0,pending=4; confirm 3 -> used=3,free=3. Write `test_quote_expiry_cannot_release_accepted_request` and `test_stale_snapshot_does_not_reset_inventory`.
- [ ] Run `python -m unittest discover -s tests -p test_market.py -v`; expect missing market module failure.
- [ ] Implement immutable revisions, RFQ response uniqueness, holds, terminal quote closure and derived inventory. Reject equal-time conflicting availability; use highest offer revision_number. Validate quote eligibility against latest capacity, not just the RFQ snapshot.
- [ ] Add `test_capacity_reduction_preserves_commitments` (used=4,total=2 -> shortfall=2,new allocation rejected); direct-request revision capacity cases; RFQ fan-out skips unavailable ships and quote quantity cannot exceed RFQ quantity. Rerun market tests expecting pass.
- [ ] Review scoped diff and record checks; commit only with authorization.

### Task 4 [P]: Explainable pure mobilisation policies

**Files:** mobilisation package and tests/test_policies.py. **Depends on:** Task 1.
**Consumes:** immutable Candidate and mission progress projections; field shapes from data model. **Produces:** MobilisationPolicy, MobilisationDecision, OfferEvaluation, select_offers with the callable contract signature.

- [ ] Write `test_earliest_arrival_uses_absolute_instant` with observations 10+5 versus 0+20 selecting the first; `test_equal_values_use_ship_id` selecting A before B; largest-capacity chooses free 6 before free 4.
- [ ] Run `python -m unittest discover -s tests -p test_policies.py -v`; expect missing policies module failure.
- [ ] Implement both sort rules and quantity limits; emit evaluations for selected and skipped candidates with immutable policy/revision basis. Skip unavailable, exhausted and oversized whole holds with reasons. No inventory mutation or I/O.
- [ ] Add `test_explanation_preserves_old_revision` and `test_selection_does_not_reserve_seats`; rerun policy tests expecting pass.
- [ ] Review scoped diff and record checks; commit only with authorization.

### Task 5: Atomic central, retries and communication dispositions

**Files:** Task 5 paths above. **Depends on:** Tasks 1–4.
**Consumes:** pure mission/market/policy rules, shared command/message models. **Produces:** RescueCentral callable API, TransactionStore, Clock, IdSource, immutable RunState, RunContext and `new_run(application_run_id: str, central_id: str) -> RunContext` in bootstrap.py. Context contains one central and its store.

- [ ] Write `test_failed_transfer_rolls_back_all_business_state`, `test_retry_after_quote_expiry_returns_original`, `test_changed_command_payload_conflicts`, `test_new_run_empty_registry` and `test_multiple_calls_preserve_history` with the contract's exact dispositions.
- [ ] Run `python -m unittest discover -s tests -p test_central.py -v`; expect missing central module failure.
- [ ] Implement transaction staging/publication, all callable operations, registry lookup, read snapshots and identity indexes. Apply pending deadline expiration before late response; unchanged terminal outcomes yield diagnostics only. Generate IDs outside domain logic; no external callbacks inside locked transitions.
- [ ] Add barrier-synchronized two-thread tests: two 4-seat quotes against total 6 produce exactly one hold; two request commands cannot exceed demand; competing responses apply one terminal transition. Inject failure after staging transfer and assert hold/request/history/command index unchanged. Assert direct requests use the same inventory boundary.
- [ ] Add import-AST test prohibiting domain imports of application/adapters/bootstrap and any third-party framework; verify all getters return isolated snapshots. Run `python -m unittest discover -s tests -v`; expect all tests pass.
- [ ] Review aggregate diff including parallel-task contracts; record checks. Commit only with authorization.

### Task 6: Reproducible experiments and demonstration

**Files:** Task 6 paths above. **Depends on:** Task 5.
**Consumes:** new_run, central API, policies and immutable scenario baselines. **Produces:** scenario/run/result models, simulate and summarize signatures from contract, plus `python -m rescue.demo` entry point.

- [ ] Write `test_delay_metrics` asserting 2+5+3 yields elapsed=10,RTT=5; `test_deadline_tie_expires_first` asserting deadline=20 and receipt=20 confirms zero; `test_repeat_seed_three_times` asserting normalized business histories/results equal across three runs.
- [ ] Run `python -m unittest discover -s tests -p test_experiments.py -v`; expect missing experiments module failure.
- [ ] Implement finite heap scheduler, seeded scripts, baseline cloning/index remapping, horizon semantics and result calculations. Process current-instant expirations before deliveries; cap scripted event generation by validated finite counts. Pure result calculation never fabricates completion time.
- [ ] Add three policy-comparison fixtures: ordinary, partial/refusal, delayed/lost/availability-change; assert unchanged operational snapshots, pending horizon reporting, None completion time when incomplete, lost delivery receipt None, duplicate message identity, and zero-delay finite termination.
- [ ] Implement demo demand=10 using partial acceptance, refusal and further mobilisation; document decisions/concurrency/availability in README. Run `python -m unittest discover -s tests -v` and `python -m rescue.demo`; expect full suite pass and C=10,P=0,complete demo output.
- [ ] Review aggregate diff and quickstart accuracy; record results. Commit only with authorization.

## Requirement traceability

| Requirements | Task owners |
| --- | --- |
| FR-001–005, FR-017–020 | 1, 2, 3, 5 |
| FR-006–007, FR-021 | 1, 2, 5 |
| FR-008, FR-022–025 | 3, 5, 6 |
| FR-009 | 4, 5 |
| FR-010–011 | 1, 5, 6 |
| FR-012–016 | 6 |
| SC-001–002, SC-007 | 2–5 |
| SC-003–006, SC-008 | 6; conceptual namespace views retained unchanged |

## Complexity Tracking

No gate violations. One transaction port exists because inventory and mission changes must publish atomically; one coarse lock is sufficient for a single in-memory process. No generic repository hierarchy, service split, event sourcing or persistence engine is introduced.

## Self-review and handoff

Checked requirement coverage, type/signature consistency, task ownership, review-focus tests and proportion against the spec. Phase 1 ends here; no implementation, tasks.md generation, commit or push performed. No after_plan hook is registered in .specify/extensions.yml. Recommended execution: subagent-driven after design review, because Tasks 2–4 have separate ownership and Task 5 needs careful integration review. The user has not yet chosen an execution method.
