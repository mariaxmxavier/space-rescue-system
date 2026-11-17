# Tasks: Rescue Web App

**Input**: [spec](spec.md), [plan](plan.md), [research](research.md), [data model](data-model.md), [UI contract](contracts/ui.md), [quickstart](quickstart.md).

**Execution**: `[P]` means eligible for concurrent work only after its named prerequisites are complete; writers own only the paths assigned to their task. Story tests are written first and demonstrated failing before their implementation. Parent integrates shared wiring. Do not commit without explicit authorisation.

## Phase 1: Setup

- [ ] T001 Inventory every operation's exact required/optional fields, nested types, enums, decimal encoding and example payloads from `rescue/api/operations.py`, `rescue/application/contracts/commands/`, `rescue/experiments/models/` and `rescue/mobilisation/models/` in `specs/013-web-app/contracts/operation-fields.md`; verify examples against the actual codec and identify policy/scenario creation fields.
- [ ] T002 [P] Select and pin exact compatible Playwright pytest and browser versions in `pyproject.toml` and `uv.lock`, and configure isolated local API/static-server browser fixtures in `tests/e2e/web/conftest.py` without changing existing test conventions.
- [ ] T003 [P] Refine an accessible operations-dashboard visual direction using the installed UI/UX Pro Max guidance, document typography, colours, focus, responsive and reduced-motion decisions in `specs/013-web-app/visual-design.md`, and avoid the unsuitable generated marketing layout.

## Phase 2: Foundation

- [ ] T004 Define and freeze exported module signatures, ownership, form registration, result rendering, event and shared-workspace interfaces in `specs/013-web-app/contracts/frontend-modules.md` after T001; ensure independent feature modules can register without editing shared files.
- [ ] T005 [P] Add browser tests for run creation, known-run reopening, run switches, concurrent stale responses, rejected calls, uncertain network outcomes and explicit history loading in `tests/e2e/web/foundation/test_workspace.py` after T002 and T004.
- [ ] T006 [P] Implement HTTP client and codec boundary in `web/shared/api/client.js` after T004: encode run IDs, send decimal strings or integers, retain all result fields, distinguish HTTP and business rejection, and never auto-retry mutations.
- [ ] T007 [P] Implement selected-run workspace and request generation guards in `web/shared/state/workspace.js` after T004: shared tabs, latest committed snapshot, refresh timestamps, stale status on failure, invalidation across run switches and out-of-order replies.
- [ ] T008 [P] Implement reusable labelled input, nested repeatable forms, result details and accessible status primitives in `web/shared/ui/controls.js` and `web/shared/ui/styles.css` after T003 and T004; keep 0, absent and empty distinct.
- [ ] T009 Implement accessible tabs, run creation/reopen and capability registration shell in `web/index.html`, `web/shell/app.js` and `web/shell/styles.css` after T005–T008; preserve a shared selected run, keyboard focus and explicit state/history controls.
- [ ] T010 Verify foundation against `tests/e2e/web/foundation/test_workspace.py` and publish the frozen contracts in `specs/013-web-app/contracts/frontend-modules.md` before dispatching feature writers.

## Phase 3: User Story 1 — Coordinate a rescue (P1)

**Independent test**: Complete the ten-person rescue, including partial acceptance, refusal and further mobilisation, ending with ten confirmed and zero pending seats.

- [ ] T011 [P] [US1] Write browser demonstration and request finality tests in `tests/e2e/web/mission/test_rescue.py`, covering registration, full/partial/refused responses, cancellation, expiration, invalid inputs and further mobilisation, after T010.
- [ ] T012 [P] [US1] Implement mission registration and authoritative progress controls in `web/missions/registration/` and `web/missions/progress/` after T010, covering station, positive demand, timing and separate confirmed/pending/unmet totals.
- [ ] T013 [P] [US1] Implement ship registration, availability and offer controls in `web/fleet/ships/`, `web/fleet/availability/` and `web/fleet/offers/` after T010, preserving versions and server outcomes.
- [ ] T014 [P] [US1] Implement direct request creation, cancellation and expiry in `web/requests/` after T010; show final outcomes and release of pending seats from server results.
- [ ] T015 [P] [US1] Implement mobilisation and decision initiation in `web/mobilisation/actions/` after T010, exposing supported policies, input fields and complete operation result.
- [ ] T016 [P] [US1] Implement response submission for full/partial acceptance and refusal in `web/communication/responses/` after T010, preserving all supported identity, sequence and timing inputs.
- [ ] T017 [US1] Register the completed US1 modules in `web/shell/app.js` after T011–T016 and run the demonstration test in `tests/e2e/web/mission/test_rescue.py`.

## Phase 4: User Story 2 — Understand the run (P1)

**Independent test**: Against a prepared run, compare mission progress, decision explanations, mission history and complete call history with authoritative records.

- [ ] T018 [P] [US2] Write browser tests for progress, nested decision details, mission history, explicit call history and failed/stale refresh in `tests/e2e/web/exploration/test_run_view.py` after T010.
- [ ] T019 [P] [US2] Implement run inspection and on-demand complete activity history in `web/exploration/run/` after T010, distinguishing mission history from call history and preserving nested response fields.
- [ ] T020 [P] [US2] Implement mission history and detailed progress inspection in `web/missions/history/` after T010, including absent and empty fields and timing values.
- [ ] T021 [P] [US2] Implement decision explanation, allocations, candidate evaluation and trace inspection in `web/mobilisation/decisions/` after T010, including all returned fields.
- [ ] T022 [US2] Register US2 modules in `web/shell/app.js` after T017 and T018–T021; verify both tabs reference the same run using `tests/e2e/web/exploration/test_run_view.py`.

## Phase 5: User Story 3 — Manage quotes and shared capacity (P2)

**Independent test**: Use two missions and one ship to hold, accept or release quotes and verify authoritative shared-capacity outcomes.

- [ ] T023 [P] [US3] Write browser tests in `tests/e2e/web/market/test_quotes.py` for quote request, recording, acceptance, rejection, expiry, version history and cross-mission overcommit rejection after T010.
- [ ] T024 [P] [US3] Implement RFQ and quote recording in `web/quotes/request/` and `web/quotes/record/` after T010 with all fields from the operation inventory.
- [ ] T025 [P] [US3] Implement quote accept, reject and expiry in `web/quotes/lifecycle/` after T010, showing request creation, held capacity release and complete results.
- [ ] T026 [P] [US3] Implement fleet revision and shared-capacity inspection in `web/fleet/inspection/` after T010, distinguishing holds, pending commitments and confirmed transport.
- [ ] T027 [US3] Register US3 modules in `web/shell/app.js` after T022 and T023–T026; run `tests/e2e/web/market/test_quotes.py`.

## Phase 6: User Story 4 — Communication and recovery (P2)

**Independent test**: Submit duplicate and out-of-order messages, inspect delivery and session state, synchronise and recover reports without duplicated seat effects.

- [ ] T028 [P] [US4] Write browser tests for duplicate, delayed and out-of-order deliveries, sequence gaps, synchronisation and report recovery in `tests/e2e/web/communication/test_recovery.py` after T010.
- [ ] T029 [P] [US4] Implement message delivery and session inspection in `web/communication/inspection/` after T010, displaying complete classifications and sequence details.
- [ ] T030 [P] [US4] Implement inbound synchronisation and report recovery controls in `web/communication/recovery/` after T010 with full identity and sequence inputs and results.
- [ ] T031 [US4] Register US4 modules in `web/shell/app.js` after T027 and T028–T030; run `tests/e2e/web/communication/test_recovery.py`.

## Phase 7: User Story 5 — Compare strategies and scenarios (P2)

**Independent test**: Configure a scenario and two policies at run creation, compare them and inspect every result and timeline with its simulated baseline identified.

- [ ] T032 [P] [US5] Write browser tests for nested policy/scenario setup, comparisons, absent configuration, baseline labelling and complete timeline in `tests/e2e/web/experiments/test_comparison.py` after T010.
- [ ] T033 [P] [US5] Implement guided nested policy and scenario editors in `web/experiments/configuration/` after T001 and T010, including baseline missions/market, response rules, availability changes, horizon, seed and event budget where supported.
- [ ] T034 [P] [US5] Implement comparison input and complete result/timeline inspection in `web/experiments/comparison/` after T010; label scenario baselines as simulated rather than live state.
- [ ] T035 [US5] Wire configuration into run creation and register comparison modules in `web/shell/app.js` after T031 and T032–T034; run `tests/e2e/web/experiments/test_comparison.py`.

## Phase 8: Polish and Verification

- [ ] T036 [P] Add keyboard-only, visible-focus, reduced-motion, screen-width 360/1440 and status-not-colour-only browser checks in `tests/e2e/web/accessibility/test_navigation.py` after T035.
- [ ] T037 [P] Update runnable setup, explicit origin configuration, exact dependency/test commands, feature walkthroughs and lost-run/history limitations in `specs/013-web-app/quickstart.md` and `docs/readme.md` after T035.
- [ ] T038 Audit all 22 operations, run creation, state/history, full result fields and all forms against `specs/013-web-app/contracts/ui.md` and `specs/013-web-app/contracts/operation-fields.md`; record evidence and gaps in `specs/013-web-app/validation.md` after T035.
- [ ] T039 Run browser suite, `make check-all` and the quickstart demonstration; record actual commands, results, accessibility checks, failures and limitations in `specs/013-web-app/validation.md` after T036–T038.

## Dependencies and Parallel Execution

Foundation T001–T010 blocks all feature implementation. T002 and T003 are independent of T001. T005–T008 have distinct paths and run after their listed prerequisites. For each story write the corresponding test first and demonstrate failure before implementing its related behaviour; parallel writers coordinate test readiness without editing one another's files. Tests and production code have separate owners.

After T010, independent implementation paths T012–T016, T019–T021, T024–T026, T029–T030 and T033–T034 may run concurrently when their story tests are red. The shell registration tasks T017, T022, T027, T031 and T035 are serial because they all edit `web/shell/app.js`. US5 configuration integrates with run creation only at T035. T036 and T037 may run in parallel after integration; T038 is read-only with its own evidence file, followed by T039 as the final writer of that file.

Story tests can use prepared API fixtures instead of requiring earlier stories' UI. US1 is the suggested MVP after foundation; US2 adds explanation, US3 market controls, US4 communication recovery and US5 comparisons. All stories are required for full scope. Architecture and seat accounting remain authoritative in the API.
