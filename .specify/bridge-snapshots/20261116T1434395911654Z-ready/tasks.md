# Tasks: Rescue Domain Model

**Input:** [plan.md](plan.md), [spec.md](spec.md), [data-model.md](data-model.md), [contracts/callable-api.md](contracts/callable-api.md), [research.md](research.md), [quickstart.md](quickstart.md), and constitution 2.1.0.
**Scope:** task generation only. All implementation tasks start unchecked. No commits, pushes, servers or external integrations are authorized by this list.
**Tests:** required by spec success criteria and constitution V. Write each story's tests first, run the targeted suite to observe the expected missing-feature failure, then implement and rerun to pass. A task is complete only after its stated check passes; test-authoring tasks complete when their intended failure is observed.
**Paths:** project-root `rescue/` and `tests/`, with CPython 3.14.10 and standard library only. No src directory or third-party dependencies.
**Format:** `- [ ] Tnnn [P?] [USn?] Description with paths`. `[P]` means disjoint ownership within an explicitly listed ready wave, not permission to ignore prerequisites. Task IDs here supersede the coarse six-task breakdown in plan.md for execution tracking.
**Contract authority:** preserve every catalogue field and relationship in data-model.md and every command signature in contracts/callable-api.md. Snapshot DTOs alias immutable capability models where shapes match; no adapter/framework objects cross inward. TransitionContext lives in rescue/values.py, never application, because domain functions consume it. No implementation may invent a missing API silently: resolve contract changes before dependent work.

## Phase 1: Setup

**Goal:** establish the exact runtime and importable project; no application behavior yet.

- [ ] T001 Pin `.python-version` to `3.14.10`, set `requires-python = "==3.14.10"` with no third-party dependencies in `pyproject.toml`, and create `rescue/__init__.py`; check `python --version` reports 3.14.10 and `python -c "import rescue"` succeeds.

- [ ] T002 Create package markers `rescue/application/__init__.py`, `rescue/mission/__init__.py`, `rescue/market/__init__.py`, `rescue/mobilisation/__init__.py`, `rescue/communication/__init__.py`, `rescue/experiments/__init__.py`, `rescue/adapters/__init__.py`, and `tests/__init__.py`; check imports succeed without business side effects. Depends on T001.


## Phase 2: Foundational contracts (blocks all stories)

**Goal:** freeze shared inputs, identity rules and application DTOs before parallel writers begin.
**Check:** run `python -m unittest discover -s tests -p test_values.py -v` and the equivalent `test_contracts.py` suite. No story implementation begins until T006 passes.


- [ ] T003 [P] Write failing normalization and immutability tests in `tests/test_values.py`: "IDs are nonblank case-sensitive strings; quantities are strict integers (bool rejected); time values are finite Decimal seconds." Assert bool/fractional/zero positive quantities reject; nonnegative zero seats for availability accepts; negative, NaN/infinite and float times reject, int and decimal-string zero accept; copied collection inputs cannot mutate snapshots. Depends on T002.

- [ ] T004 [P] Write failing DTO contract tests in `tests/test_contracts.py` for every command and Result field in `contracts/callable-api.md`, required fields, optional defaults, unknown-field rejection, and snapshot immutability; "Optional values use None, never fabricated zero timestamps." Depends on T002.

- [ ] T005 Implement `Id`, `Instant`, normalization, typed domain validation errors, and frozen `TransitionContext(event_id, at, reason, message_id=None)` in `rescue/values.py`; preserve nonblank IDs without trimming and use finite nonnegative Decimal seconds. Run `tests/test_values.py` to pass. Depends on T003.

- [ ] T006 Implement shared command dataclasses and `Result[T]` in `rescue/application/contracts.py` with exact signatures/status/reason values from `contracts/callable-api.md`; use deferred type imports for future capability snapshot types. Run `tests/test_contracts.py` and `tests/test_values.py` to pass. Depends on T004–T005.


## Phase 3: US1 — Coordinate seats safely (P1, MVP)

**Goal:** callable coordination, terminal outcomes, shared capacity safety and per-run lifecycle.
**Independent test:** demand 10; request 6 then accept 4 -> confirmed=4,pending=0,additional_needed=6; pending 6 blocks another request; confirming 6 completes. Quotes alone never complete. Competing missions never overbook.
**Contracts:** register_mission, register_ship, publish_availability, publish_offer, request_quotes, record_quote, accept_quote, create_request, reject_quote, expire_quotes, record_response, cancel_request, expire_request, get_progress, get_history; basic mobilise is included to satisfy constitutional strategy requirements. Timing detail and explanation enhancements follow in US2/US3.


- [ ] T007 [P] [US1] Write failing pure tests in `tests/test_mission.py` for all six outcomes, partial finality, fixed demand, invalid confirmation quantities, insufficient mission demand and progress. Assert request 6/accept 4 closes with C=4,P=0 and exactly one creation plus one outcome history entry; 10 pending never completes. Depends on T006.

- [ ] T008 [P] [US1] Write failing market tests in `tests/test_market.py` for RFQ fan-out, zero-or-one quote response, held->pending->confirmed counted once, rejected/expired hold release, direct-request capacity checks and revision ordering. Assert total=6,held=4 -> pending=4 -> partial confirmation=3 gives used=3,free=3; old snapshot/revision publication cannot reset reservations. Depends on T006.

- [ ] T009 [P] [US1] Write failing central/concurrency tests in `tests/test_central.py` and `tests/test_concurrency.py`: one central per context, multiple independent mission IDs, state retained between calls, fresh-run empty registry/history, retry/duplicate/conflict safety, unknown request diagnostics, and staged-transfer failure retaining hold with no request/history/index. Barrier-synchronize two 4-seat quote attempts against total=6 and assert exactly one applies. Depends on T006.

- [ ] T010 [P] [US1] Implement `Mission`, `MissionData`, `SeatRequest`, `RequestHistoryEntry`, `MissionProgress` in `rescue/mission/models.py`, retaining all catalogue fields. Enforce "demand is a positive integer fixed on registration", "Station and ship names must be nonblank", "Full quote quantity transfers intact", and "Direct requests require an immutable offer-revision basis." Quotes/revisions/decisions are optional links; request deadline, response receipt and closed time are optional. Depends on T007.

- [ ] T011 [P] [US1] Implement Ship, B3Market, ShipAvailability, SeatRFQ, RFQOffer, ShipOffer, ShipOfferRevision and ShipUsage in `rescue/market/models.py`; retain catalogue fields. Enforce "Total seats may be zero to represent exhausted capacity; positive quantities are required for offers, RFQs and requests", "available=False blocks new allocations regardless of total", "Arrival duration is nonnegative", "An offer is positive and no larger than requested_seats", quote states "held, accepted, rejected, expired", RFQ states "pending, quoted, expired", and "An accepted quote links to exactly one request; all other quotes link to none." Depends on T008.

- [ ] T012 [P] [US1] Implement `register`, `add_request`, `apply_outcome`, `progress` in `rescue/mission/rules.py` using exact contract signatures and TransitionContext; derive C/P, enforce C>=0,P>=0,C+P<=D and terminal finality. Enforce "History has unique event_id and consecutive mission_sequence starting at 1", "Exactly one entry per applied create or terminal transition", "Ignored deliveries add no applied entries." Run `tests/test_mission.py` to pass. Depends on T010.

- [ ] T013 [P] [US1] Implement `usage`, `hold_quote`, `transfer_quote`, `close_quote` and snapshot/offer publication rules in `rescue/market/rules.py`. Derive usage from holds and request commitments; choose latest availability by recorded_at, reject same-time conflicting snapshots, current offer by highest positive revision_number. Require caller quote expiry > recorded_at with no default TTL; accepted/rejected/expired quotes are terminal. Reduce capacity without erasing commitments, expose shortfall and block new allocations; quote transfer requires no shortfall. Run `tests/test_market.py` to pass. Depends on T011.

- [ ] T014 [P] [US1] Implement frozen `CommunicationMessage` and `MessageDelivery` in `rescue/communication/models.py`; "Its deliveries have distinct IDs and positive attempt numbers; loss has received_at=None", "Payloads are typed immutable values, not arbitrary executable objects." Preserve logical message identity across attempts and unresolved request IDs for diagnostics. Add constructor checks in `tests/test_contracts.py`. Depends on T006.

- [ ] T015 [US1] Define `TransactionStore.transact`, Clock.now, IdSource.next_id in `rescue/application/ports.py` and frozen RunState in `rescue/application/state.py` using domain-owned values; include central identity, registry, market, command/message/delivery indexes and policy/scenario/result registries. No live mutable mappings escape. Depends on T010–T014.

- [ ] T016 [US1] Implement atomic staged-state publication under one lock in `rescue/adapters/memory.py`, constructing one central/store per `new_run(application_run_id, central_id)` RunContext in `rescue/bootstrap.py`. Test transaction exceptions leave original state unchanged and synchronized reads expose complete snapshots in `tests/test_concurrency.py`; no global singleton or GIL assumption. Depends on T015.

- [ ] T017 [US1] Implement US1 callable methods in `rescue/application/central.py` per `contracts/callable-api.md`, delegating transitions to Mission and coordinating full hold transfer, direct allocation, history and successful-command index atomically. Key request retries by run+command_id, compare complete normalized business payload excluding retry now; replay original result before expiry checks, reject altered content. Record per-delivery diagnostics separately; first valid terminal decision wins, unknown/late/conflicting messages do not rewrite outcomes. Expire at deadline before applying a response. Run central/concurrency suites to pass. Depends on T009,T012–T016.

- [ ] T018 [P] [US1] Implement frozen MobilisationPolicy, Candidate, DecisionContext, MobilisationDecision and OfferEvaluation in `rescue/mobilisation/models.py` and pure `select_offers` in `rescue/mobilisation/policies.py`; earliest absolute arrival then ship ID, largest free capacity then arrival then ship ID, demand caps, whole-quote skips and immutable revision basis. Add `tests/test_policies.py` assertions 10+5 beats 0+20, free 6 beats 4 and A beats B on ties. This is the basic strategy needed for the MVP. Depends on T012–T013.

- [ ] T019 [US1] Wire basic `mobilise` and consistent progress/history reads in `rescue/application/central.py`; selection records a proposal without reserving capacity, caller submits request commands and allocation revalidates latest state. Expand `tests/test_central.py` for two missions, repeated requests per ship, failed transfers, demand immutability and held quotes not pending/confirmed. Run all US1 suites via `python -m unittest discover -s tests -v`; expect pass. Depends on T017–T018.


## Phase 4: US2 — Explain decisions and changing offers (P2)

**Goal:** preserve historical revision basis and explain all selection and rejection decisions.
**Independent test:** create a request against capacity 30 then publish capacity 10; original request and basis stay unchanged. Inspect policy revision, every candidate, ranks, quantities and selected/skipped reasons. Retry yields the original request; changed content conflicts.


- [ ] T020 [P] [US2] Write failing policy/explanation tests in `tests/test_policies.py` for unavailable/exhausted/oversized-held candidates, unique ranks and selected/skipped reasons; "Selection has one immutable policy revision and evaluations with unique rank and one revision basis each." Assert selection mutates no inventory and retains previous revisions. Depends on T019.

- [ ] T021 [P] [US2] Write US2 integration tests in `tests/test_central.py`: capacity 30->10 leaves request quantity and basis intact; reverse revision timestamps leave greatest revision_number current; shortfall blocks new allocations; retry after closure/quote expiry replays with no extra history, cross-mission identity reuse conflicts. Applied entries and delivery diagnostics remain distinct. Depends on T019.

- [ ] T022 [US2] Complete explainable evaluation fields and reason codes in `rescue/mobilisation/models.py` and `rescue/mobilisation/policies.py`, preserving "Never overwrite that basis on later revisions." Run `tests/test_policies.py` to pass. Depends on T020.

- [ ] T023 [US2] Complete revision/decision linkage and history/disposition queries in `rescue/application/central.py`, with immutable snapshots of all considered revisions and preserved command fingerprints; extend market rules only if needed for revision conflicts in `rescue/market/rules.py`. Run `tests/test_central.py` and `tests/test_policies.py` to pass. Depends on T021–T022.


## Phase 5: US3 — Understand waiting and deadlines (P2)

**Goal:** expose waiting/response metrics and deterministic deadline handling with a controlled clock.
**Independent test:** submission 10, receipt 17 -> elapsed 7; no receipt -> response elapsed None and waiting grows. Deadline 20/receipt 20 -> expiration, zero new confirmation and late diagnostic.


- [ ] T024 [P] [US3] Write failing timing/deadline tests in `tests/test_timing.py` covering optional deadlines, deadline <= submission rejection, response before submission rejection, no-response None, cancellation before delivery, and receipt exactly/after 20 expiration before response. Assert released demand becomes available without reopening closed requests. Depends on T019.

- [ ] T025 [US3] Implement read-only waiting/response timing projections in `rescue/mission/models.py` and `rescue/mission/rules.py`; "Response timestamps cannot precede submission; closure is never earlier than submission", "With no response, response_elapsed is None and waiting=now-submitted_at", "No response_received_at is invented for cancellation/expiry." Keep timing in explicit Decimal instants and arrival estimates distinct. Depends on T024.

- [ ] T026 [US3] Complete explicit expiry/deadline enforcement and timing DTO exposure in `rescue/application/central.py` and `rescue/application/contracts.py` using the supplied clock/time; identity retries precede new effects, at/after deadline closes once and classifies delivery late. Run `tests/test_timing.py` and all prior suites to pass. Depends on T025 and US2 integration T023 (shared writer files).


## Phase 6: US4 — Compare what-if outcomes (P3)

**Goal:** reproducible policy comparisons using isolated baseline copies and result summaries.
**Independent test:** run both policies from the same versioned baseline three times per seed; normalized histories/results match, operational mission/market state remains identical, incomplete results have no completion time.
**Increment boundary:** deterministic scripted responses and fixed delays are supported here; loss/duplication/reordering configuration is completed in US5. This lets US4 validate without a circular dependency on US5.


- [ ] T027 [P] [US4] Write failing scenario/isolation/comparison tests in `tests/test_experiments.py`: baseline holds, requests, history and identity indexes are copied, same seed repeated three times reproduces normalized results, horizon-time events process before stopping, incomplete completion time is None and outstanding requests remain visible. Depends on T026.

- [ ] T028 [P] [US4] Write failing metric tests in `tests/test_results.py` for confirmed/unmet totals, request count, cumulative released pending quantities (may exceed demand), no-confirmation arrival None, common run-start arrival reference and no successful ranking for incomplete runs. Depends on T026.

- [ ] T029 [US4] Implement RescueScenario, CommunicationProfile, SimulationRun, SimulationResult, RunSnapshot and scripted event values in `rescue/experiments/models.py`; preserve catalogue fields. Enforce "positive finite horizon and nonnegative integer seed", "Reject unknown ship references, negative delays and unbounded event-generation rules", "A run has no result while running and exactly one when completed or horizon_reached." Versioned baseline/profile data are immutable; None metrics remain unknown. Depends on T027–T028.

- [ ] T030 [P] [US4] Implement finite heap timeline in `rescue/experiments/timeline.py`, ordered by `(instant, priority, scenario_sequence, insertion_sequence)` with expiration priority 0 and other events 1; process horizon-time events before stopping and reject unbounded zero-delay generation. Add `tests/test_timeline.py` for ties/horizon/budget validation, then run it to pass. Depends on T029.

- [ ] T031 [P] [US4] Implement `summarize(run: RunSnapshot) -> SimulationResult` in `rescue/experiments/results.py` from exact data-model formulas: confirmation time only when complete, latest confirmed arrival minus run start, pending-release totals excluding conversion to confirmed. Run `tests/test_results.py` to pass. Depends on T029.

- [ ] T032 [US4] Implement `simulate(scenario, policy, run_id)` in `rescue/experiments/runner.py` using a fresh bootstrap context, isolated copied baseline values and remapped scoped indexes, run-local seeded Random, stable request ordinal scripts and finite scheduler. No real sleeps or operational store writes; finish as completed or horizon_reached. Run `tests/test_experiments.py` to pass. Depends on T030–T031.

- [ ] T033 [US4] Add typed scenario/policy configuration inputs at `new_run` in `rescue/bootstrap.py` for immutable initial registries, retaining its existing two required identity arguments; implement `compare(ComparePolicies)` in `rescue/application/central.py` from a consistent baseline snapshot, execute independent runs outside the operational lock, and return isolated results. Add `tests/test_comparison.py` for two policies and ordinary/partial-refusal fixtures; results must not alter operational state. Depends on T032.


## Phase 7: US5 — Exercise unreliable communication (P3)

**Goal:** scripted delays, loss, duplicate attempts and reordered messages without repeated business effects.
**Independent test:** outbound 2 + decision 5 + return 3 -> response elapsed 10 and RTT 5; duplicate one response, lose another and delay one past deadline, preserving terminal decisions and allowing remobilisation. Unreachable completion stops at horizon.


- [ ] T034 [P] [US5] Write failing communication simulation tests in `tests/test_communication.py`: exact 2+5+3 metrics, zero valid delay, loss received_at=None, duplicates sharing message identity but distinct delivery IDs, reordered conflicting/unknown responses, cancellation before delivery and expiry before equal-time response. Depends on T033.

- [ ] T035 [P] [US5] Write failing resilience comparison tests in `tests/test_resilience.py` using delayed/lost responses plus changing availability; assert remobilisation after release, pending horizon state, same-seed three-run equality, finite zero-delay duplicates and unchanged operational mission/market snapshots. Depends on T033.

- [ ] T036 [US5] Complete CommunicationProfile loss/duplication/reordering script validation in `rescue/experiments/models.py` and immutable message payload/delivery dispositions in `rescue/communication/models.py`; preserve logical identity across all attempts, reject changed payload for same message ID and changed data for same delivery ID, use typed finite scripts. Depends on T034–T035.

- [ ] T037 [US5] Implement outbound/decision/return scheduling, scripted/seeded loss, duplicate attempts, reordering and distinct RTT/response timing in `rescue/experiments/timeline.py` and `rescue/experiments/runner.py`; propagate every delivery to diagnostics through the central and never silently drop closed-request attempts. Run `tests/test_communication.py`, `tests/test_resilience.py`, `tests/test_timeline.py` and all experiment suites to pass. Depends on T036.


## Phase 8: Polish and cross-cutting evidence

**Goal:** enforce inward dependencies and deliver the documented end-to-end demonstration.


- [ ] T038 [P] Add AST import-boundary tests in `tests/test_architecture.py`: mission/market/mobilisation/communication models and rules must not import application/adapters/bootstrap, read environment, instantiate persistence or invoke wall clocks/network; application must not import concrete memory adapter. Experiment runner is application-level orchestration and may depend on bootstrap; experiment models/results remain pure. Run architecture suite to pass. Depends on T037.

- [ ] T039 [P] Create `rescue/demo.py` and `tests/test_demo.py` for demand 10 with multiple ships, partial acceptance, refusal, remobilisation and confirmed-only completion; assert output C=10,P=0,complete. Include two-policy comparison over ordinary, partial/refusal and delayed/lost/changing-capacity scenarios. Run `python -m rescue.demo` and demo tests to pass. Depends on T037.

- [ ] T040 Update `README.md` with exact setup/test/demo commands, inward architecture, retry scope, concurrency lock/staged publication, strategy tie-breakers, capacity shortfalls and time/expiry assumptions; align `specs/001-rescue-domain-model/quickstart.md` with actual APIs and demonstration. Preserve conceptual namespace meaning and existing ER/UML associations. Depends on T038–T039.

- [ ] T041 Run `python -m unittest discover -s tests -p "test_*.py" -v`, `python -m rescue.demo` and `git diff --check`; execute every scenario in `specs/001-rescue-domain-model/quickstart.md`, record actual commands/results in `specs/001-rescue-domain-model/validation.md`, and map FR-001–FR-025 plus SC-001–SC-008 to passing evidence. Do not mark implementation complete if any required check fails. Depends on T040.


## Dependencies and execution order

Setup T001 -> T002; foundation `(T003 || T004) -> T005 -> T006` (T005 only needs T003; T006 joins both test branches).

| Story | Entry prerequisites | Completion gate | Increment |
| --- | --- | --- | --- |
| US1 | T006 | T019 | Safe callable MVP with basic selection, history and retry handling |
| US2 | T019 | T023 | Full explanation and changing-offer evidence |
| US3 | T019; integration waits for T023 | T026 | Timing projections and deadline evidence |
| US4 | T026 (therefore US1/US2) | T033 | Deterministic isolated comparison |
| US5 | T033 | T037 | Unreliable communication and resilience comparisons |
| Polish | T037 | T041 | Complete required evidence and runnable demo |

Story graph: `Setup -> Foundation -> US1 -> (US2, US3 test preparation) -> US3 integration -> US4 -> US5 -> Polish`.

The stories share rescue rules and a callable central, so claiming full cross-story write independence would be unsafe. Each remains independently testable at its checkpoint without requiring later stories. US3 test authoring may overlap US2, but shared central/models/contracts writes are serialized. New deadline behavior must preserve the US1 terminal-outcome contract.

Within US1: `(T007 || T008 || T009)` precedes implementation; `T010 -> T012`, `T011 -> T013`, and T014 can execute on separate paths. T015 joins completed domain models/rules; T016 -> T017; T018 may overlap T016/T017 after domain rules are ready. T019 joins central and strategy work. No concurrent worker edits another task's tests or package markers.

## Parallel execution examples

- **Foundation:** T003 owns tests/test_values.py while T004 owns tests/test_contracts.py; join before production contracts.
- **US1:** first author T007/T008/T009 in separate test files. Then mission worker T010/T012 owns rescue/mission; market worker T011/T013 owns rescue/market; communication worker T014 owns rescue/communication and, after foundation is complete, its specified test_contracts.py additions. T018 policy writer can overlap T016/T017 because paths are disjoint and domain contracts are frozen.
- **US2:** T020 policy tests and T021 central tests may run together. Production changes T022 and T023 follow tests in sequence.
- **US3:** T024 can run alongside US2 implementation because tests/test_timing.py is separate; T025 waits for mission/market wave completion and T026 waits for US2 central integration. No concurrent central writers.
- **US4:** T027/T028 test authors own different files; after T029, T030 timeline and T031 result calculation have separate ownership and can run together. Runner/comparison integration follows their join.
- **US5:** T034/T035 tests can run together; T036/T037 implementation is sequential because profile and delivery schema must settle before scheduling.
- **Polish:** T038 boundary tests and T039 demonstration own separate files; README/quickstart follows passing behavior.

`[P]` labels describe eligible waves, not mandatory agent dispatches. Future execution must follow start-work and repository sandbox/worktree rules, with explicit path ownership and no commits without user authorization.

## Verification commands and checkpoints

For any named test file, use `python -m unittest discover -s tests -p test_NAME.py -v`; all cases must pass after production implementation. Each test-first task must first fail for the intended missing behavior, not an interpreter/configuration error. Use deterministic barriers for concurrency tests, never probabilistic sleeps. Re-run prior story suites at every story checkpoint. Full suite and demo are required at T041.

## Requirement coverage

| Requirements | Tasks |
| --- | --- |
| FR-001–004 | T003–T008, T010–T013, T017–T019 |
| FR-005 | T009, T014–T017, T021, T024–T026, T034–T037 |
| FR-006–009 | T010–T014, T017–T023 |
| FR-010–011 | T024–T026, T030, T034–T037 |
| FR-012–013 | T027–T033, T035–T037 |
| FR-014 | T034–T037 |
| FR-015–016 | T027–T033, T035–T037 |
| FR-017–020 | T007, T009–T010, T012, T015–T019 |
| FR-021–022 | T008, T011, T013, T017, T021–T023 |
| FR-023–024 | T008–T009, T011, T013, T016–T017, T019 |
| FR-025 | T010–T011, T027, T029, T032–T033, T035, T040 |
| SC-001–002 | T007–T023 |
| SC-003–004 | T027–T037, T039 |
| SC-005 | T024–T026, T034–T037 |
| SC-006 | T027, T032–T035 |
| SC-007 | T009, T016–T019 |
| SC-008 | T027, T032–T035, T040 |

## Implementation strategy

1. Deliver Setup + Foundation + US1 (T001–T019) as the MVP. Validate its callable tests; no experiments are needed to prove seat safety.
2. Add US2 explanations and US3 timing as independently verified increments; do not duplicate rescue rules.
3. Add US4 baseline comparison, then US5 unreliable communication; both use isolated run contexts.
4. Finish architecture checks, demo and quickstart evidence. A handoff status of ready records artifact readiness only; it does not mean tests passed, the draft specification was ratified, an execution method was chosen, or implementation was authorized by this command.

No automatic commit tasks are included. No task is complete merely because a subagent stopped; parent verification and explicit task tracking updates are required during execution.
