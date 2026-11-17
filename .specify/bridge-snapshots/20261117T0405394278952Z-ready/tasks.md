# Tasks: Mobilisation Conformance

**Input**: `specs/006-mobilisation-conformance/{spec.md,plan.md,research.md,data-model.md,quickstart.md,contracts/}` and `.specify/memory/constitution.md`.
**Prerequisites**: Roadmap dependency 002 is implemented. Inspect current mission/market vocabulary before starting; 004 and 005 are not prerequisites. Use the existing isolated worktree and the repository's start-work protocol for implementation. Do not commit, push, or open a PR without explicit authorisation.
**Tests**: Required by FR-006, FR-010 and SC-001–SC-006. Write new behaviour tests first and observe their intended failures before implementation. Preserve existing tests through each migration.
**Organisation**: Setup → foundation → US1 (P1) → US2 (P1) → US3 (P2) → US4 (P2) → final verification. All paths below are relative to the repository root.

## Format: `[ID] [P?] [Story] Description`

`[P]` denotes independent files within a dependency-ready batch, not permission to skip prerequisites. Story labels map to the specification. Every task includes its owned paths; shared configuration and registry edits are serial.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish a reproducible baseline and verify the exact solver dependency before algorithm work.

- [ ] T001 Verify uv 0.13.8 and Python 3.14.10 against `pyproject.toml` and `.python-version`, run `make install` and `make check-all`, and record baseline results plus the current worktree/main commit identities in `specs/006-mobilisation-conformance/quickstart.md`; capture `uv run python -m rescue.demo` stdout as raw bytes in a temporary location outside the repository for T044.
- [ ] T002 Add `ortools==9.15.6755` to runtime dependencies in `pyproject.toml`, regenerate `uv.lock` with the pinned uv, run `uv sync --locked`, and smoke-import `SimpleMinCostFlow`, `CpModel`/`CpSolver` and `KnapsackSolver` using the exact module paths in `specs/006-mobilisation-conformance/research.md`; record outcomes in `specs/006-mobilisation-conformance/quickstart.md` and stop solver work if the pinned platform cannot import them.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Freeze observable behaviour and provide shared scenario inputs before reorganising production files.

- [ ] T003 Extend `tests/unit/mobilisation/policies/test_policies.py` to characterise current earliest-arrival/largest-capacity ranking, absolute arrival, static and dynamic skip-reason precedence, evaluation IDs/ranks, demand including pending and confirmed seats, full held quotes, and empty/no-help inputs; retain these assertions when the file moves in T015.
- [ ] T004 Create reusable immutable candidate, quote, mission and decision-context fixtures in `tests/unit/mobilisation/conftest.py` for empty inputs, covered demand, exhausted/unavailable ships, invalid/expired holds, oversized holds, deterministic ties, partial capacity and indivisible under-coverage; keep fixture construction free of application wiring and clocks.

**Checkpoint**: Baseline is recorded and existing behaviour has executable assertions. US1 may begin. No persistent application state or market/mission rules change.

## Phase 3: US1 — A reader understands each part from its own file (P1)

**Goal**: Split existing entities without changing the existing selection function or public model imports.
**Independent test**: Existing policy tests and full suite pass after replacing `models.py`; each persisted Mobilisation diagram entity maps to one documented file.

### Tests

- [ ] T005 [US1] Add focused model invariant tests in `tests/unit/mobilisation/models/test_policy.py`, `test_candidate.py`, `test_decision_context.py`, `test_offer_evaluation.py` and `test_decision.py`; assert existing constructor failures, tuple immutability, unique/contiguous ranks, selected/skipped views and compatibility of `from rescue.mobilisation.models import X`.

### Implementation

- [ ] T006 [US1] Replace `rescue/mobilisation/models.py` with `rescue/mobilisation/models/__init__.py`, `policy.py`, `candidate.py`, `decision_context.py`, `offer_evaluation.py` and `decision.py`; preserve constructor signatures, normalisation, existing invariants and re-exports, explicitly retaining `revision ≥ 1`, `free_seats ≥ 0`, `quote: RFQOffer?`, `allocatable_seats = min(free_seats, revision.capacity)` and `unique ids`; keep shared private normalisation local or import it from its owning module without circular imports.
- [ ] T007 [US1] Add what/when/why docstrings to every existing mobilisation module, class and public function in `rescue/mobilisation/__init__.py`, `rescue/mobilisation/models/` and `rescue/mobilisation/policies.py`; name the Mobilisation UML/ER class and diagram paths in each persisted entity module, and mark candidate/context as transient.
- [ ] T008 [US1] Add a focused entity/file mapping and docstring-presence check in `tests/architecture/mobilisation/test_documentation.py` using the Mobilisation diagrams under `docs/architecture/diagrams/rescue-domain-model/namespaces/Mobilisation/`; verify what/when/why content manually, run T005 and the full suite, and record the US1 checkpoint in `specs/006-mobilisation-conformance/quickstart.md`.

**Checkpoint**: US1 can be delivered on its own; the old policy entrypoint still works. New allocation types belong to US2.

## Phase 4: US2 — The decision does not depend on which algorithm chose (P1)

**Goal**: Make policy vocabulary closed, introduce a functional allocator boundary, and preserve default decisions and the demo.
**Independent test**: Swap injected allocators without changing decision shape/reason precedence; reject malformed results and unknown policy strategies; greedy default reproduces baseline.

### Tests

- [ ] T009 [P] [US2] Extend `tests/unit/mobilisation/models/test_policy.py` and add `test_algorithm_name.py`, `test_skip_reason.py`, `test_allocation.py` and `test_trace_step.py` under `tests/unit/mobilisation/models/`; test all six allowed strategy names, string/key-value policy encodings, rejection during construction, `seats ≥ 0`, `allocation order = rank order`, trace immutability, and static skip precedence at quote expiry boundaries.
- [ ] T010 [P] [US2] Create `tests/unit/mobilisation/algorithms/test_allocator_contract.py` parametrised over registry entries, initially the two greedy strategies; assert allocator contract rules 1–7, including every input exactly once, zero for static skips, per-ship/demand bounds, quote indivisibility, deterministic ship-ID ties, one trace step per candidate and final `result`, using T004 fixtures.
- [ ] T011 [P] [US2] Create `tests/unit/mobilisation/services/test_decide.py` with injected valid and malicious allocators; test duplicate/missing/foreign candidates, negative/over-capacity/over-demand seats, split quotes, allocation to static skips, existing input validation, reason precedence followed by `not_chosen`, evaluation identity/ranks, and DEBUG records with trace fields on logger `rescue.mobilisation`.

### Implementation

- [ ] T012 [US2] Add `rescue/mobilisation/models/algorithm_name.py`, `skip_reason.py`, `allocation.py` and `trace_step.py` and update `policy.py`, `candidate.py` and `__init__.py`: implement the exact closed set `earliest_arrival`, `largest_capacity`, `priority_queue`, `min_cost_flow`, `cp_sat`, `knapsack`; resolved `strategy` must be an `AlgorithmName`, else construction fails; preserve policy encodings and default behaviour, add `arrival_instant(candidate)`, and enforce `seats ≥ 0`, `allocation order = rank order`, `detail: tuple[tuple[str, str], ...]` and `immutable` trace data. Use the exact SkipReason values from `data-model.md`, with `static_skip_reason(candidate, at)` returning the first three (`unavailable`, `quote_not_held`, `expired_quote`).
- [ ] T013 [US2] Create the callable `Allocator` alias and initial two-entry `ALLOCATORS` registry in `rescue/mobilisation/algorithms/__init__.py`, and implement `rescue/mobilisation/algorithms/greedy/allocate.py` plus package `__init__.py`; preserve earliest-arrival `(arrival, ship_id)` and largest-capacity `(-allocatable, arrival, ship_id)` ordering, full held quotes, zero allocations for every skipped candidate, and trace inputs/order/picks/skips/final result. Keep the three-argument allocator signature via separate functions or bound configuration, with no I/O or clock.
- [ ] T014 [US2] Implement `select_offers` in `rescue/mobilisation/services/decide.py` and add `services/__init__.py`; accept an injected allocator mapping defaulting to `ALLOCATORS`, validate inputs, obtain unmet demand, call the configured allocator and reject breaches of allocator rules 1–5 with `DomainValidationError` before constructing a decision. Explain zero allocations in static-reason order then `insufficient_demand`, `exhausted`, `quote_exceeds_remaining_demand`, `insufficient_capacity`, `not_chosen`; log every trace step with structured DEBUG extras, and preserve existing decision fields, IDs, rank order and default output.
- [ ] T015 [US2] Change only the selection import in `rescue/application/central.py` to `rescue.mobilisation.services.decide`, remove `rescue/mobilisation/policies.py`, and migrate `tests/unit/mobilisation/policies/test_policies.py` into `tests/unit/mobilisation/services/test_decide.py` without losing its assertions; adjust `tests/architecture/mobilisation/test_documentation.py` for the removed module and new public types/functions.
- [ ] T016 [US2] Add `mobilisation-peers-one-way`, `mobilisation-allowed-imports`, `mobilisation-layers` and `mobilisation-solver-isolated` to `pyproject.toml` as specified in `contracts/import-contracts.md`; retain all three existing contracts, permit services to reach OR-Tools indirectly through algorithms while forbidding direct solver imports in services/models, and verify `make check-architecture`.
- [ ] T017 [US2] Update `tests/architecture/boundaries/test_architecture.py` to validate all seven contracts including the new layers contract rather than assuming three forbidden contracts; add one isolated temporary-package seeded violation per new contract in `tests/architecture/boundaries/test_mobilisation_contracts.py`, assert each named contract fails, and leave the real source tree untouched by seeding.
- [ ] T018 [US2] Add greedy-specific regression tests in `tests/unit/mobilisation/algorithms/test_greedy.py` and run the decision, model, contract, architecture and full regression suites; compare demo stdout bytes against T001 and record the independently working US2 checkpoint in `specs/006-mobilisation-conformance/quickstart.md`.

**Checkpoint**: US1 + US2 form the useful MVP: documented models, closed policy names, a checked allocator boundary and both legacy strategies. Additional names may be constructed but must not be advertised as runnable until T028 registers their implementations.

## Phase 5: US3 — Five algorithms can be compared on the same scenarios (P2)

**Goal**: Supply all five algorithm families, trace each decision, and compare their results and timings on identical scenarios.
**Independent test**: All six registry entries (five families plus legacy largest-capacity) pass shared contracts; default comparison prints five rows per scenario with coverage and all four required measures, exposing knapsack shortfalls.

### Algorithm tests (independent files; all depend on T018)

- [ ] T019 [P] [US3] Add `tests/unit/mobilisation/algorithms/test_priority_queue.py` covering equality to greedy for the same snapshot, recomputation after availability changes, deterministic ties, held quotes, empty/covered demand and trace order.
- [ ] T020 [P] [US3] Add `tests/unit/mobilisation/algorithms/test_min_cost_flow.py` covering maximum covered seats before arrival cost, greedy preallocation of eligible held quotes, exhausted/oversized quotes, ties, zero residual demand, solver statuses and chosen-first rank/trace output.
- [ ] T021 [P] [US3] Add `tests/unit/mobilisation/algorithms/test_cp_sat.py` covering maximum coverage then minimum last arrival then fewest ships, native whole-quote constraints, equal-optimum ship-ID ties, empty/infeasible/status paths, deterministic repeated results and chosen-first trace output.
- [ ] T022 [P] [US3] Add `tests/unit/mobilisation/algorithms/test_knapsack.py` covering whole allocatable offers or quoted seats only, non-fitting offers, maximum covered seats without overshoot, visible under-coverage, tied alternatives, solver-result branches and chosen-first trace output.

### Algorithm implementations (parallel by folder after corresponding failing tests)

- [ ] T023 [P] [US3] Implement `rescue/mobilisation/algorithms/priority_queue/allocate.py` and `__init__.py` using `heapq.heapify`/pop on `(arrival, ship_id)` with the same seat/quote rules as greedy and allocator-contract traces; rebuild from each input snapshot without persistent mutable queue state.
- [ ] T024 [P] [US3] Implement `rescue/mobilisation/algorithms/min_cost_flow/allocate.py` and `__init__.py` using `SimpleMinCostFlow`: allocate eligible held quotes greedily by arrival first, then source→ship→sink arcs with allocatable capacities, arrival-minus-decision-time costs and residual demand supply; call `solve_max_flow_with_min_cost`, handle statuses explicitly, return selected ships then unselected ships sorted by `(arrival, ship_id)` within each group, and trace model/quote choices/status/result.
- [ ] T025 [P] [US3] Implement `rescue/mobilisation/algorithms/cp_sat/allocate.py` and `__init__.py` using `x_i ∈ [0, cap_i]`, `use_i ∈ {0,1}`, `x_i ≤ cap_i·use_i`, `x_i ≥ use_i`, quoted `x_i = q_i·use_i` and `Σx ≤ D`; maximise covered seats, fix coverage then minimise `T·(n+1) + Σuse` with `T ≥ arrival_i·use_i`. Use `num_workers=1`, `random_seed=0`, enforce ship-ID tie resolution without changing these primary objectives, handle solver statuses, and return chosen-first rank order plus model/status/pick/skip/result traces.
- [ ] T026 [P] [US3] Implement `rescue/mobilisation/algorithms/knapsack/allocate.py` and `__init__.py` using OR-Tools branch-and-bound `KnapsackSolver`: sorted `(arrival, ship_id)` items with weight=value=full allocatable seats or full valid quote, capacity=demand, zero for ineligible items; retain whole-ship choices and deterministic ship-ID ties, return chosen-first rank order and trace item/model/solver/pick/skip/result steps.
- [ ] T027 [P] [US3] Complete the greedy family's explanatory trace coverage in `rescue/mobilisation/algorithms/greedy/allocate.py` and its edge-case assertions in `tests/unit/mobilisation/algorithms/test_greedy.py`; retain both legacy orderings and verify that each considered input and the final result appear in the trace without changing baseline allocation.
- [ ] T028 [US3] Register all six `AlgorithmName` entries in `rescue/mobilisation/algorithms/__init__.py` after T023–T027, extend `tests/unit/mobilisation/algorithms/test_allocator_contract.py` to exercise every entry on all T004 fixtures, and assert registry completeness and all shared rules including deterministic tie outcomes rather than only sorted presentation.

### Comparison tests and implementation

- [ ] T029 [P] [US3] Create `tests/unit/mobilisation/services/test_compare.py` with fake clocks and supplied scenarios/allocators; assert one row per requested scenario/algorithm, `scenario`, `algorithm`, `seats_covered`, nullable `last_seat_arrival_s`, `ships_used`, `unused_seats` over chosen ships only, and `runtime_ms`, including no-selection and under-coverage cases and observable trace logging.
- [ ] T030 [P] [US3] Create `tests/e2e/benchmarks/compare/test_compare_cli.py` invoking `python -m benchmarks.mobilisation.compare` in a subprocess; test the default five families, table columns/row counts, exit success, and `--trace` JSON-lines with algorithm/step/ship/detail fields and final results. Ignore timing values in deterministic output assertions and do not launch a server.
- [ ] T031 [US3] Implement pure `compare(scenarios, allocators, clock)` in `rescue/mobilisation/services/compare.py` returning the contract's metrics rows, exercising the checked decision path so trace logging is retained, and measuring elapsed milliseconds with the injected callable only; report last selected arrival relative to decision time (empty if none), selected-ship unused seats and actual covered seats.
- [ ] T032 [US3] Add `benchmarks/__init__.py`, `benchmarks/mobilisation/__init__.py` and `benchmarks/mobilisation/compare.py` as the executable module; define reproducible five-ship scenarios for splittable demand, tied arrivals, held quotes, insufficient supply and knapsack under-coverage, select earliest-arrival/priority-queue/min-cost-flow/CP-SAT/knapsack by default, inject `time.perf_counter`, and configure DEBUG JSON-lines logging with `--trace` while normal output prints only the table.
- [ ] T033 [US3] Add `compare` and `compare-trace` targets and `.PHONY` entries in `Makefile`, include `benchmarks` in both lint and format commands, and run T029/T030 plus shared allocator tests; record per-algorithm five-ship timing (<1 s) and total comparison timing (<10 s) in `specs/006-mobilisation-conformance/quickstart.md` as measured evidence, keeping wall-clock thresholds outside deterministic unit tests.

**Checkpoint**: Each family passes the common safety boundary and produces comparable metrics and trace data. `largest_capacity` remains available through the registry without becoming a sixth default comparison row.

## Phase 6: US4 — The choice of algorithms is recorded (P2)

**Goal**: Bring existing decision/research drafts and per-algorithm explanations into agreement with the working implementations.
**Independent test**: A reader can follow indexed links to the rationale and all five methods, reproduce each worked allocation, and identify assumptions, trade-offs and the default without reading implementation code.

- [ ] T034 [P] [US4] Write `rescue/mobilisation/algorithms/greedy/README.md` and `diagram.mmd` explaining earliest-arrival and legacy largest-capacity, a worked partial-allocation/quote example, actual sorting complexity, tie-breaking and trace interpretation.
- [ ] T035 [P] [US4] Write `rescue/mobilisation/algorithms/priority_queue/README.md` and `diagram.mmd` with a worked heap example, heapify/pop complexity, snapshot rebuilding and its limitations for incremental availability changes, deterministic ordering and traces.
- [ ] T036 [P] [US4] Write `rescue/mobilisation/algorithms/min_cost_flow/README.md` and `diagram.mmd` with the seat/cost network, worked allocation, actual solver complexity with sources, deterministic ordering and the explicit limitation that held quotes are preallocated greedily rather than optimised as indivisible flow.
- [ ] T037 [P] [US4] Write `rescue/mobilisation/algorithms/cp_sat/README.md` and `diagram.mmd` with the implemented constraints, two-stage objective, ship-ID tie resolution, worked example, solver status handling, worst-case complexity and trace interpretation.
- [ ] T038 [P] [US4] Write `rescue/mobilisation/algorithms/knapsack/README.md` and `diagram.mmd` with a worked shortfall example, whole-offer semantics and chosen-seat unused-capacity interpretation, deterministic tie-breaking and complexity of the implemented branch-and-bound solver rather than an unimplemented dynamic-programming algorithm.
- [ ] T039 [US4] Reconcile existing `docs/architecture/decisions/0001-mobilisation-algorithms.md` and `docs/reference/mobilisation-algorithms-research.md` with measured implementation behaviour, solver APIs and algorithm complexity; keep earliest-arrival as default, retain the per-mission scope and limitations, verify source links against primary documentation, and retain Proposed status unless acceptance is explicitly authorised.
- [ ] T040 [US4] Update `docs/readme.md` to retain ADR/research links and add links to `specs/006-mobilisation-conformance/quickstart.md` and all five algorithm READMEs (which link their diagrams); update `README.md` with strategy assumptions, availability-snapshot handling and comparison/trace commands, and verify all new-document links and worked examples.

**Checkpoint**: US4's rationale is discoverable and accurate; existing ADR/research work is extended rather than duplicated.

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T041 [P] Update `docs/architecture/diagrams/rescue-domain-model/namespaces/Mobilisation/class-diagram.mmd` with the six-value `AlgorithmName` enum and the policy selection-resolution note, regenerate `class-diagram.svg` through the diagram rendering workflow, and check the unchanged entity relationship diagram still matches the split entity files.
- [ ] T042 Audit every module, class and public function under `rescue/mobilisation/` for what/when/why docstrings, including new algorithms/services/types; complete documentation in its owning file, update `tests/architecture/mobilisation/test_documentation.py` as needed, and confirm diagram mapping remains one file per persisted entity.
- [ ] T043 Run branch coverage for `rescue/mobilisation/` through `uv run pytest --cov=rescue.mobilisation --cov-branch --cov-report=term-missing --cov-fail-under=100`; close every uncovered line/branch using meaningful rule/status tests in `tests/unit/mobilisation/models/`, `algorithms/` and `services/`, then rerun `make check-all` and all four seeded-contract cases in `tests/architecture/boundaries/test_mobilisation_contracts.py`.
- [ ] T044 Follow `specs/006-mobilisation-conformance/quickstart.md` end to end using `make install`, `make check-all`, `make compare` and `make compare-trace`; compare raw demo stdout bytes to T001 (and main if the recorded main baseline matches), check no unintended package behaviour changed, and record command results, 100% line/branch coverage, five-family row counts, timings and baseline identity there. Correct the illustrative trace algorithm value to the actual closed vocabulary and document any measured limitation without weakening acceptance criteria.

## Dependencies & Execution Order

```text
T001 → T002 → T003 → T004
  → US1: T005 → T006 → T007 → T008
  → US2: (T009 | T010 | T011) → T012 → T013 → T014 → T015 → T016 → T017 → T018
  → US3: (T019 | T020 | T021 | T022)
           → (T023 | T024 | T025 | T026 | T027) → T028
           → (T029 | T030) → T031 → T032 → T033
  → US4: (T034 | T035 | T036 | T037 | T038) → T039 → T040
  → T041 → T042 → T043 → T044
```

- Setup and foundation block every story. US1 preserves the old selection entrypoint and is independently releasable.
- US2 depends on US1's model package. The default greedy implementation moves into US2 so its behaviour can be verified before adding other solvers; this deliberately refines the plan's five-folder parallel batch.
- US3 depends on US2's checked allocator boundary. T023 depends on T019, T024 on T020, T025 on T021, and T026 on T022. Run T027 with those implementations only after T018. T028 alone owns the shared registry.
- US4 can be assessed as documentation alone using the existing design, but final worked examples and complexity claims depend on completed US3 implementations. The listed delivery order finishes it after US3.
- T041 is independent of algorithm README writing and may run alongside T034–T038. T042 waits for all production files. T043/T044 are the final acceptance gate; never mark them complete on targeted checks alone.
- `pyproject.toml`, `uv.lock`, `Makefile`, `docs/readme.md`, the registry and each shared test file have one writer at a time. Parallel writers own only the files named by their task. Do not revert unrelated work.

## Parallel Execution Examples per Story

- **US1**: T006's six package files require coordinated replacement of `models.py` and are serial. After T006, docstring review of `candidate.py`/`decision_context.py` may run alongside review of `offer_evaluation.py`/`decision.py` within T007, with ownership explicitly partitioned; do not parallelise the package re-exports.
- **US2**: After T008, run T009 (model tests), T010 (shared allocator tests) and T011 (decision-service tests) concurrently. Join before T012; T015 later merges the old policy test file into the service test file with one writer.
- **US3**: After T018, write T019–T022 concurrently, then run the four implementations T023–T026 and greedy trace work T027 concurrently with separate algorithm folders/test files. Join before T028; T029 and T030 can subsequently run concurrently.
- **US4**: Run T034–T038 concurrently, one algorithm README/diagram pair per writer, optionally alongside T041's namespace diagram update. Join before T039 reconciles the shared rationale and T040 edits the shared index.

## Implementation Strategy

1. Establish setup/foundation evidence. Reuse the pinned toolchain and existing architecture gates; introduce no additional runtime library beyond the planned exact OR-Tools dependency.
2. Deliver US1 first, verifying compatibility through the existing tests. Deliver US2 as the useful MVP: interchangeable functions, checked results, preserved legacy strategies, and unchanged demo output. US1 alone is the smaller documentation/layout increment.
3. Add US3 algorithm folders in bounded independent batches, then register them serially and build the pure comparison service and clock-owning CLI. Measure safety, coverage and objective outcomes separately from machine-dependent timing.
4. Finish US4 with worked examples and evidence-backed rationale, then update the model diagram and run all acceptance checks. Keep all implementation checkboxes unchecked during task generation.

## Requirement Coverage

| Requirement / success criterion | Tasks |
|---|---|
| FR-001 / SC-001 entity files and diagrams | T005–T008, T041–T042 |
| FR-002 docstrings | T007–T008, T012–T014, T023–T027, T031, T042 |
| FR-003 shared allocator and checked decision | T010–T015, T028 |
| FR-004 closed vocabulary and legacy default | T009, T012–T015, T018, T044 |
| FR-005 five folders and explanations | T013, T023–T027, T034–T038 |
| FR-006 / SC-002 shared safety contracts | T010–T011, T019–T028 |
| FR-007 / SC-004 declared boundaries and seeded failures | T016–T017, T043 |
| FR-008 / SC-003 comparison and four measures | T029–T033, T044 |
| FR-009 rationale and indexed research | T039–T040 |
| FR-010 / SC-006 full suite and unchanged demo | T001, T003, T018, T043–T044 |
| SC-005 100% mobilisation line/branch coverage | T005, T009–T011, T018–T022, T029, T043 |

## Notes

- Algorithms return pure trace data; services log it, and only `benchmarks/mobilisation/compare.py` configures output and owns a real clock.
- All allocations include every input once, even when skipped. Bounds and indivisible held quotes are enforced before recording any decision.
- Solver failure branches and deterministic equal-optimum choices require explicit evidence; seeded randomness or sorted output alone does not prove ship-ID tie-breaking.
- No task authorises cross-mission optimisation, storage changes, altered market/mission rules, commits, pushes or PR creation.
