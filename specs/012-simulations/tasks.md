# Tasks: Composed Mission Simulations

**Input**: [plan](plan.md), [spec](spec.md), [data model](data-model.md), [contracts](contracts/simulation.md), [timeline](contracts/timeline.md).
**Tests**: Required by the constitution and plan; implement each meaningful behavior test-first within its owning task. All boxes remain unchecked until parent verification.
**[P]**: Allowed only after listed dependencies pass, with disjoint writer scopes from [execution-handoff.md](execution-handoff.md). Never edit another worker's files or shared initializers.

## Phase 1 - Setup

- [x] T001 [P] Repair trusted runtime nested-type resolution in rescue/api/codec.py; add tests/integration/api/http/test_nested_commands.py for valid availability/offer/envelope payloads, malformed fields and the solver-proposal-to-request lifecycle. Domain rules and API result shapes must stay unchanged. Verify the focused HTTP tests. (5 focused tests passed; review approved.)
- [x] T002 [P] Prepare the simulations package skeleton and parent-owned initializers in simulations/; add pydantic==2.14.3 to pyproject.toml and refresh uv.lock without upgrading dependencies. Update Makefile, pyproject.toml import-linter/coverage settings and tests/architecture/boundaries/test_architecture.py for the new package, retaining all existing coverage floors. Reserve every __init__.py for this owner. Verify locked sync and dependency/import configuration. (18 contracts kept; architecture tests and Ruff passed; review approved.)

## Phase 2 - Frozen foundations

- [ ] T003 Implement the contracts in simulations/models/ and MissionApiABC in simulations/adapters/ports/mission_api.py, plus one fake in tests/unit/simulations/support/fake_mission_api.py and model tests in tests/unit/simulations/models/. Follow data-model.md verbatim: immutable strict models, extra='forbid', tuples, one mission, finite Decimal>=0 time, positive demand excluding bool, 200 events, horizon100, two-member batches. Include typed request/response projections, twelve situation IDs, event ordering and submit=False solver rounds. Freeze and review the interface before parallel dependents start.

## Phase 3 - US1: Combined timeline (P1)

**Goal**: one mission containing all twelve situations with real solver-driven requests.
**Independent check**: all12 against the HTTP API shows12/12 evidence and complete10/0; post-completion replay still runs.

- [ ] T004 [P] [US1] Implement simulations/adapters/http/mission_api.py and focused tests/unit/simulations/adapters/test_http_api.py plus tests/integration/simulations/http/test_round_trip.py. Use MissionApiABC, operation-specific typed values, lossless decimal strings, get_progress/get_session/get_deliveries/state, retries=0, trust_env=False, connect/pool2s and read/write10s. Implement max-two-client concurrent invocation with cleanup and no promised hard wall-clock deadline. Depends T001/T003.
- [ ] T005 [P] [US1] Implement simulations/services/run_scenario.py and simulations/services/solver_round.py with tests/unit/simulations/services/test_timeline.py and test_solver_round.py using the shared fake. Consume selected evaluations in rank order, bind real request IDs, process (time,phase,ordinal), observe after events, prevent empty solver loops, support explicitly deferred proposal submission, drain events after completion and fail missing evidence/bounds. Depends T003; no edits under situations/scenarios.
- [ ] T006 [P] [US1] Implement situation recipes under simulations/services/situations/rescue/completion/, rescue/remobilisation/ and requests/closure/ with tests/unit/simulations/situations/rescue/ and requests/. Cover full confirmation, partial-and-refusal, cancellation and expiration using symbolic request selectors and evidence predicates. Depends T003.
- [ ] T007 [P] [US1] Implement situation recipes under simulations/services/situations/communication/delivery/ and communication/ordering/ with tests/unit/simulations/situations/communication/. Cover exact-message replay, deadline-late receipt and actual session sequence gaps/obsolete deliveries; correction after invalid sequence uses the next sequence. Depends T003; no HTTP calls in recipes.
- [ ] T008 [P] [US1] Implement situation recipes under simulations/services/situations/safety/validation/, safety/finality/, safety/concurrency/ and availability/shortfall/, availability/updates/ with tests/unit/simulations/situations/safety/ and availability/. Competing B2 requests copy one selected solver evaluation with distinct command IDs; one applies, one rejects insufficient_capacity. Overconfirm3 on request2 must reject invalid_input. Availability cannot erase settled commitments. Depends T003.
- [ ] T009 [US1] Compose simulations/services/scenarios/all_twelve.py and tests/integration/simulations/timeline/test_all_twelve.py using the exact timeline contract: A4/B4/C2, demand10, temporary6-confirmed shortfall4, replacement closures, final B2/C2, correction3->2, complete10/0 and replay afterward. Use real API JSON via injected TestClient; never patch annotations or bypass codec in the final test. Depends T001/T004/T005/T006/T007/T008. Verify all twelve evidence predicates within one mission.

## Phase 4 - US2: Vary the combination (P1)

**Goal**: all11/all10/baseline reuse the same runner and recipes.
**Independent check**: the variants execute one mission each, observe exactly declared sets and repeat without prior-state collisions.

- [ ] T010 [P] [US2] Implement simulations/services/scenarios/eleven.py, ten.py, baseline.py and catalogue.py with tests/unit/simulations/scenarios/test_composition.py. all11 omits concurrency; all10 also omits message replay; baseline fully confirms A4/B4/C2. Check unique IDs, valid recipe dependencies, no scenario-per-situation catalogue, declared counts12/11/10/1, unknown-profile preflight and fresh-identity isolation. Depends T009; reserve all_twelve.py from edits.
- [ ] T011 [P] [US2] Add tests/integration/simulations/timeline/test_variants.py and test_repeatability.py exercising model-driven profiles through TestClient, incomplete-final-state expectations through an injected fixture, missing evidence, exhausted event budget and continuing independent profiles after failure. Depends T009; may use contract-defined fixtures for forthcoming T010 modules, but final test execution waits T010. No shared conftest/initializer edits.

## Phase 5 - US3: Explain execution (P2)

**Goal**: terminal output follows solver execution and makes failures understandable.
**Independent check**: CLI list does no I/O; run shows all requests/decisions/progress, failures and final evidence counts.

- [ ] T012 [P] [US3] Implement simulations/entrypoints/cli.py, render.py and simulations/__main__.py with tests/unit/simulations/entrypoints/test_cli.py and test_render.py. Follow the CLI contract: list/run/--all, loopback default, streaming observations, logical times and batch slots, IDs/quantities/reasons, final pass/fail independent of mission status; exit0/1/2. Inject writer and adapter; no network on list/invalid names. Depends T004/T005/T010/T011.
- [ ] T013 [P] [US3] Add tests/architecture/simulations/test_layers.py and test_import_safety.py to enforce pure models, adapter inward direction, service injection, no rescue imports and no import-time I/O. Confirm the new Makefile gates include simulations without weakening rescue floors. Depends T002/T003; can run alongside T004-T012 after those prerequisites.
- [ ] T014 [P] [US3] Add tests/e2e/simulations/timeline/test_live_timeline.py and its local conftest.py for --simulation-base-url, plus tests/integration/simulations/cli/test_command.py for default full-timeline coverage through TestClient. Mark real-server tests live_http; ask parent to register the marker and select not live_http in default gates. Explicit -m live_http without its URL fails clearly. Run live all12/all11/all10/baseline after CLI integration. Depends T009/T010/T012; owns only these test subtrees.

## Phase 6 - Integration and verification

- [ ] T015 Update README.md, docs/readme.md and specs/012-simulations/quickstart.md with implemented commands, selected/excluded situations, solver proposal/submission distinction, temporary shortfall, HTTP prerequisite and output interpretation. Integrate parent-owned package exports/configuration and the final gate wiring in Makefile/pyproject.toml. Depends T001-T014; preserve concurrent spec013 material.
- [ ] T016 Run make install and make check-all, existing demo, and the explicit live E2E plus four CLI profiles against an already-running API. Record commands, per-layer branch coverage>=80%, exit codes and actual outcomes in specs/012-simulations/validation.md. Fresh final reviewer checks aggregate uncommitted diff, spec compliance and quality; fix findings before marking complete. No commits/push/PR. Depends T015.

## Dependencies and parallel examples

T001 || T002 -> T003 -> {T004,T005,T006,T007,T008,T013} -> T009 -> {T010,T011} -> T012 -> T014 -> T015 -> T016. T013 may finish independently before T009. T011 may author contract-based tests concurrently with T010; do not claim they pass until T010 is integrated. The parent owns all shared files and integrates exports between waves.

US1: adapter, runner and three situation groups run in parallel after T003; each owns its matching tests. US2: catalogue/variants and integration expectations run in parallel after all12. US3: architecture checks run independently once foundations exist, while CLI work waits for catalogue integration. [P] is not permission to bypass a prerequisite or overlap files.

## Implementation strategy

MVP is US1 with the comprehensive all12 timeline, not twelve isolated scripts. Add variants, then terminal UX/live checks. Prepare start-work and isolated implementation workspace first; derive the bridge adapter from canonical tasks.md. Fresh bounded workers receive a task brief, frozen interfaces, exact owned paths and report path. The parent verifies task reviews and test evidence before changing checkboxes. Do not execute implementation from this planning turn merely because tasks are now written.
