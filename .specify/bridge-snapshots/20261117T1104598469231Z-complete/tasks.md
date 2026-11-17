# Tasks: Experiments Conformance

**Input**: `plan.md`, `spec.md` (user stories US1–US4), `data-model.md`, `contracts/`, `research.md`, `quickstart.md`

**Tests**: included. FR-008 and FR-009 require them, and the plan delivers test-first. Each class or step task writes its test first (red), then the code (green). Existing tests use `unittest.TestCase`; new tests follow the same style.

**Organization**: by user story. US1 (injection) runs first on the old `runner.py`, so the import cycle is gone before any file moves. US2 splits the files. US3 splits the simulation into steps, on top of US2's foundation. US4 (diagrams) only needs US2. Polish integrates and verifies.

## Format: `- [ ] TID [P?] [Story?] Description with path`

- **[P]**: different files, no dependency on an unfinished task. Dispatch these to parallel subagents together.
- **[Story]**: US1–US4, only in story phases.
- Every task names the files it owns. Two `[P]` tasks never share a file.

## Path conventions

- Source: `rescue/experiments/` (`E` = `rescue/experiments/`)
- Unit tests: `tests/unit/experiments/{models,timeline,results,simulation}/`
- Architecture tests: `tests/architecture/experiments_layout/`
- Diagrams: `docs/architecture/diagrams/rescue-domain-model/` (`D`)

## Rules every task keeps

- Behaviour does not change (FR-010). Move code as it is; keep every error message.
- In the simulation, these never change order: `rng` draws, `next(sequence)` (formerly `next_sequence()`), and `id_source.next_id(...)` (research R3).
- Every new module, class and public function gets the docstring in `contracts/docstring.md`; private helpers get `What:` and `Why:` only.
- No function in `E/simulation/` exceeds 60 lines (SC-002).

---

## Phase 1: Setup

**Purpose**: capture the baseline so later steps can be proven to change nothing.

- [x] T001 Set `UV_PYTHON` to a GIL CPython 3.14.10 build if the first Python on PATH is free-threaded (research R8). Run `make install` and `make check-all` on the clean checkout and record the result. Save the demo output with `uv run python -m rescue.demo > <scratchpad>/demo-before.txt`.
- [x] T002 Capture the seeded snapshot fixture before any code change. Write a small script in the scratchpad that imports `scenario_value` and `policy_value` from `tests/unit/experiments/simulation/test_experiments.py`, runs `simulate(scenario_value(), policy_value(), run_id="FIXTURE")`, and writes `repr(snapshot)` to `tests/unit/experiments/simulation/fixtures/seeded_snapshot.txt`. Do the same for `scenario_value(horizon=10, seed=7)` into `seeded_snapshot_seed7.txt`. These files are the byte-identity reference for FR-010. Also capture `scenario_value()` with a `ScriptedResponse` for `SHIP-1` ordinal 1 (`partially_accepted`, no seat count) and a `CommunicationProfile` with `reordering_rule=(1,)` into `seeded_rng_scenario.txt`, because it is the only fixture that reaches `rng.randint`. Note: the seed-41 and seed-7 fixtures are identical, so they do not prove seed sensitivity.

---

## Phase 2: Foundational

**Purpose**: none beyond Setup. US1 deliberately runs on the unsplit code; the foundation for the split belongs to US2 (T013–T016).

---

## Phase 3: User Story 1 - The simulation gets its run by injection (Priority: P1) 🎯 MVP

**Goal**: `rescue/experiments/` never imports `rescue.bootstrap`; `simulate` takes `start_run`; `RescueCentral` gets it from `bootstrap.new_run`; the import cycle is gone.

**Independent Test**: `make check-architecture` reports `Contracts: 13 kept, 0 broken.`; `grep -rn "rescue.bootstrap" rescue/experiments` prints nothing; `uv run pytest tests/integration/application tests/unit/experiments` passes and the seeded snapshots equal the T002 fixtures.

- [x] T003 [US1] Write the failing tests first: in `tests/unit/experiments/simulation/test_experiments.py`, add `test_seeded_runs_match_the_main_fixture` (runs both fixture scenarios with `start_run=new_run` and compares `repr` with the T002 files), `test_start_run_is_required` (calling without `start_run` raises `TypeError`) and `test_non_callable_start_run_is_rejected` (`start_run=None` raises `DomainValidationError`). Pass `start_run=new_run` at the 3 existing `simulate` calls in that file (lines ≈201, 202, 222, 230).
- [x] T004 [P] [US1] Create the ports in `rescue/experiments/simulation/ports/start_run.py` (`StartRun`), `run_handle.py` (`RunHandle`) and `simulation_central.py` (`SimulationCentral`), plus `ports/__init__.py` re-exporting the three, and `rescue/experiments/simulation/__init__.py` re-exporting them. Each is a `typing.Protocol` with exactly the members in `contracts/start-run.md`. `SimulationCentral` types its 5 methods with commands and `Result` from `rescue.application.contracts`. `RunHandle` types `store: TransactionStore` and `id_source: IdSource` from `rescue.adapters.ports`. Do not import `rescue.application.central` or `rescue.bootstrap`.
- [x] T005 [US1] Edit `rescue/experiments/runner.py`: replace `from rescue.bootstrap import new_run` with a keyword-only required parameter `start_run: StartRun` on `simulate`. Reject a non-callable value with `DomainValidationError("simulate requires a callable start_run")`, checked after the policy check. Call `start_run(...)` with the same arguments `new_run` received. Depends on T003, T004.
- [x] T006 [US1] Edit `rescue/application/central.py`: add the required field `start_run: StartRun` after `id_source` on the frozen `RescueCentral` dataclass. At module top, import `simulate` from `rescue.experiments.runner` and `StartRun` from `rescue.experiments.simulation`. Delete the function-local import at the `compare` method (≈line 1034) and pass `start_run=self.start_run` to `simulate`. Depends on T005.
- [x] T007 [US1] Edit `rescue/bootstrap.py`: pass `start_run=new_run` when building `RescueCentral` (≈line 71). Depends on T006.
- [x] T008 [P] [US1] Edit `rescue/demo.py`: pass `start_run=new_run` at the `simulate` call (≈line 182). Depends on T005.
- [x] T009 [P] [US1] Edit `tests/integration/application/communication/test_communication.py`: pass `start_run=new_run` at all 8 `simulate` calls and import `new_run` from `rescue.bootstrap`. Depends on T005.
- [x] T010 [P] [US1] Edit `tests/integration/application/resilience/test_resilience.py`: pass `start_run=new_run` at all 3 `simulate` calls and import `new_run`. Depends on T005.
- [x] T011 [US1] Edit `pyproject.toml` per `contracts/import-contracts.md`: add `rescue.experiments.timeline` to the sources of `domain-outward` and `domain-io`; add the contracts `experiments-pure-core` and `experiments-no-bootstrap` verbatim. Until US2 creates the `timeline` package, `rescue.experiments.timeline` resolves to `timeline.py`, and `rescue.experiments.simulation` to the package created in T004. Depends on T005.
- [x] T012 [US1] Edit `tests/architecture/boundaries/test_architecture.py`: assert `Contracts: 13 kept, 0 broken.`; add `rescue.experiments.timeline` to `domain_sources`; add the 2 new rows to the reviewed table. Run `make check-all`; it must be green, and the seeded tests of T003 must pass. Depends on T007–T011.

**Checkpoint**: the import cycle is broken and behaviour is unchanged. This is the MVP: it can merge alone.

---

## Phase 4: User Story 2 - Find and understand any experiments part fast (Priority: P1)

**Goal**: one class per file in `models/scenario/`, `models/run/` and `timeline/`; `summarize` in `results/`; every part carries the four-part docstring; existing import paths keep working.

**Independent Test**: `uv run pytest tests/unit/experiments/models tests/unit/experiments/timeline tests/unit/experiments/results tests/architecture/experiments_layout/test_docstrings.py tests/architecture/experiments_layout/test_one_public_name_per_file.py`. The architecture tests pass only after T042.

### Foundation for the split (serial)

- [x] T013 [US2] Move the old modules aside: `git mv rescue/experiments/models.py rescue/experiments/models/_legacy.py`, `timeline.py` → `timeline/_legacy.py`, `results.py` → `results/_legacy.py`, `runner.py` → `simulation/_legacy.py` (the `simulation/` folder already exists from T004). Fix the internal imports inside the moved files to the new `_legacy` paths only. Depends on T012.
- [x] T014 [US2] Write the package `__init__.py` files so every existing import path resolves: `models/__init__.py` re-exports the 7 classes from `_legacy`; `timeline/__init__.py` re-exports `Timeline` and `TimelineEvent`; `results/__init__.py` re-exports `summarize`; `simulation/__init__.py` adds `simulate` from `_legacy` to the 3 ports. `models/scenario/__init__.py` and `models/run/__init__.py` hold a docstring only. Set each `__all__` to the names in `contracts/public-imports.md`. Switch `central.py`, `demo.py` and the 3 test files from `rescue.experiments.runner` to `rescue.experiments.simulation`. Depends on T013.
- [x] T015 [US2] Create `rescue/experiments/models/_validation.py` (private): move `_frozen_tree` and `_finite_tuple` from `models/_legacy.py` as `frozen_tree` and `finite_tuple`, unchanged, keeping every error message. `_legacy.py` imports them from here. Depends on T014.
- [x] T016 [P] [US2] Create `tests/architecture/experiments_layout/test_one_public_name_per_file.py`, adapted from `tests/architecture/mission_layout/test_one_public_name_per_file.py`. Root `rescue/experiments`; each non-`__init__`, non-underscore module defines exactly one public top-level class or function; the four `__all__` lists equal `contracts/public-imports.md`; no function in `rescue/experiments/simulation/` exceeds 60 lines (`end_lineno - lineno + 1`). Mark `xfail(strict=True, reason="until T042")`.
- [x] T017 [P] [US2] Create `tests/architecture/experiments_layout/test_docstrings.py`, adapted from the mission one. Root `rescue/experiments`; same labels and order; every `Diagram:` path exists. Mark `xfail(strict=True, reason="until T042")`.

### One class or function per file (parallel, after T015)

Each task: write the test first, moving the matching tests from the old test file, then create the file with its docstring. Field constraints are verbatim from `data-model.md`.

- [x] T018 [P] [US2] `rescue/experiments/models/scenario/run_baseline.py` (`RunBaseline`) + `tests/unit/experiments/models/test_run_baseline.py`. Fields `missions: tuple[Mission]`, `market: B3Market`, `command_index`, `message_index`, `delivery_index`, `decision_index`; `__post_init__` moved unchanged.
- [x] T019 [P] [US2] `rescue/experiments/models/scenario/scripted_response.py` (`ScriptedResponse`) + `tests/unit/experiments/models/test_scripted_response.py`. Fields `ship_id`, `request_ordinal`, `outcome`, `confirmed_seats = None`.
- [x] T020 [P] [US2] `rescue/experiments/models/scenario/communication_profile.py` (`CommunicationProfile`) + `tests/unit/experiments/models/test_communication_profile.py`. Fields `profile_id`, `ship_id`, `outbound_delay_seconds`, `decision_delay_seconds`, `return_delay_seconds`, `loss_rule`, `duplication_rule`, `reordering_rule`. Move `test_negative_communication_delay_and_unbounded_profile_rule_are_rejected` here.
- [x] T021 [US2] `rescue/experiments/models/scenario/rescue_scenario.py` (`RescueScenario`) + `tests/unit/experiments/models/test_rescue_scenario.py`. Fields `scenario_id`, `revision`, `name`, `baseline: RunBaseline`, `response_rules: tuple[ScriptedResponse]`, `availability_changes: tuple[ShipAvailability]`, `time_horizon_seconds`, `seed`, `event_budget`, `communication_profiles: tuple[CommunicationProfile] = ()`. Move `test_horizon_seed_and_event_budget_are_bounded` and `test_unknown_ship_references_are_rejected` here. Depends on T018–T020.
- [x] T022 [P] [US2] `rescue/experiments/models/run/simulation_result.py` (`SimulationResult`) + `tests/unit/experiments/models/test_simulation_result.py`. Fields `completed`, `confirmed_seats`, `unmet_demand`, `requests_sent`, `released_seats`, `confirmation_elapsed_seconds = None`, `latest_arrival_estimate_seconds = None`.
- [x] T023 [US2] `rescue/experiments/models/run/simulation_run.py` (`SimulationRun`) + `tests/unit/experiments/models/test_simulation_run.py`. Fields `run_id`, `scenario_id`, `scenario_revision`, `policy_id`, `policy_revision`, `started_at`, `finished_at`, `status`, `result: SimulationResult | None`. Depends on T022.
- [x] T024 [US2] `rescue/experiments/models/run/run_snapshot.py` (`RunSnapshot`) + `tests/unit/experiments/models/test_run_snapshot.py`. Fields `run: SimulationRun`, `missions`, `market`, and the four indexes. Depends on T023.
- [x] T025 [P] [US2] `rescue/experiments/timeline/timeline_event.py` (`TimelineEvent`) + `tests/unit/experiments/timeline/test_timeline_event.py`. Constraint: `priority = None` resolves to 0 for `expire`, else 1; blank `kind` is rejected. Move `test_expiration_priority_is_defaulted_to_zero_and_other_events_to_one` here.
- [x] T026 [US2] `rescue/experiments/timeline/timeline.py` (`Timeline`) + `tests/unit/experiments/timeline/test_timeline.py` (rewrite the existing file to import from the new path; keep its 4 remaining tests). Constraints: heap order `(instant, priority, scenario_sequence, insertion order)`; `peek_next`/`pop_next` return `None` past the horizon; the `event_budget + 1`th `schedule` raises `DomainValidationError`. Depends on T025.
- [x] T027 [P] [US2] `rescue/experiments/results/summarize.py` (`summarize` plus its private helpers `_revision` and `_arrival_instant`) + `tests/unit/experiments/results/test_summarize.py`, moving the 3 tests from `test_results.py`. Depends on T024 for imports only; it may start against `models/__init__` re-exports.

**Checkpoint**: every model, timeline and result name has its own file and test; `_legacy.py` still backs the package `__init__`s until T042.

---

## Phase 5: User Story 3 - The simulation loop reads in steps (Priority: P2)

**Goal**: `simulate` composes named steps that take state explicitly; no closures, no `nonlocal`.

**Independent Test**: `uv run pytest tests/unit/experiments/simulation` passes; each step test builds a small input by hand (a `Timeline`, a `random.Random(seed)`, an `itertools.count(1)`, and a stub `RunHandle` where needed); the seeded fixture test from T003 still passes.

- [x] T028 [US3] Create `rescue/experiments/simulation/_payload.py` (`_ResponsePayload`, moved unchanged) and `rescue/experiments/simulation/session.py` (`SimulationSession`, a frozen dataclass with `handle: RunHandle`, `policy: MobilisationPolicy`, `timeline: Timeline`, `rng: random.Random`, `sequence: Iterator[int]`, `response_rules: Mapping[tuple[str, int], ScriptedResponse]`, `profiles: Mapping[str, CommunicationProfile]`, `ship_ordinals: dict[str, int]`) + `tests/unit/experiments/simulation/test_session.py`. Depends on T014.
- [x] T029 [P] [US3] `rescue/experiments/simulation/scripted_outcome.py` (`scripted_outcome(rule, request_seats, rng)`, from `_scripted_response`) + `test_scripted_outcome.py`: a table over refused, accepted with `None` seats, partial with `None` seats (`request_seats` 1 → refused; >1 → `rng.randint(1, n-1)`), and specified seats 0, partial and full.
- [x] T030 [P] [US3] `rescue/experiments/simulation/install_baseline.py` (`install_baseline(handle, baseline, run_id)` and `baseline_identity_ids(baseline)`, with private `_copy_command_index`) + `test_install_baseline.py`. Test that command index entries of length 5 get the new run id, and that identity ids are collected from `_id` fields and the command and delivery indexes, sorted. `baseline_identity_ids` is the one allowed second public name in this file; add it to the T016 test's allowlist.
- [x] T031 [P] [US3] `rescue/experiments/simulation/schedule_response.py` (`schedule_response(session, rule, mission, request, ordinal, profile, message_id)`, from `_schedule_response`) + `test_schedule_response.py`: no profile (zero delays); lost (`received_at None`); duplicated (two events, attempts 1 and 2); reordered (priority 2). Depends on T028, T029.
- [x] T032 [P] [US3] `rescue/experiments/simulation/schedule_request_events.py` (`schedule_request_events(session, mission_id, request)`) + `test_schedule_request_events.py`: an expire event when a deadline exists; the ship ordinal increments; a response is scheduled only when a rule matches; `next_id("message")` is called only then. Depends on T031.
- [x] T033 [P] [US3] `rescue/experiments/simulation/schedule_initial_events.py` (`schedule_initial_events(session, baseline, scenario, started_at)`) + `test_schedule_initial_events.py`: mobilise events for every mission, then availability changes shifted by `started_at`, then baseline pending requests (expire at `max(started_at, deadline)`, then response). Keep the original order of `next(sequence)`. Depends on T031.
- [x] T034 [P] [US3] `rescue/experiments/simulation/mobilise_mission.py` (`mobilise_mission(session, mission_id, now)`) + `test_mobilise_mission.py`: returns early when `additional_needed == 0`; raises `DomainValidationError("scenario mobilisation failed: …")` when the selection is not applied; creates one request per selected evaluation and calls `schedule_request_events` for each applied request. Depends on T032.
- [x] T035 [P] [US3] `rescue/experiments/simulation/events/publish_availability.py`, `events/expire_request.py` and `events/record_response.py`, each with one function `(session, event, now)` moved from the matching `while` branch, plus `events/__init__.py`, plus `tests/unit/experiments/simulation/events/test_publish_availability.py`, `test_expire_request.py` and `test_record_response.py`. Expiry and the first response attempt reschedule `mobilise` at `now`; a failed publication raises with the same message. Depends on T028.
- [x] T036 [US3] `rescue/experiments/simulation/play_event.py` (`play_event(session, event)`: dispatch by `event.kind` to `mobilise_mission` or the 3 handlers; an unknown kind raises `DomainValidationError(f"unknown scenario event kind: {kind!r}")`) + `test_play_event.py`. Depends on T034, T035.
- [x] T037 [P] [US3] `rescue/experiments/simulation/finish_run.py` (`finish_run(handle, scenario, policy, run_id, started_at, finished_at, status)`: provisional run, snapshot, `summarize`, finalised run) + `test_finish_run.py`. Depends on T028.
- [x] T038 [US3] `rescue/experiments/simulation/simulate.py` (`simulate`): validate; compute `started_at` and `horizon`; call `start_run`; `install_baseline`; build the session (`itertools.count(1)`, `random.Random(scenario.seed)`); `schedule_initial_events`; loop `pop_next` → `play_event` → completion check (all missions `confirmed == people_count` and the next event later than now ⇒ `completed`); `finish_run`. At most 60 lines; move the completion check into a private `_all_complete` if needed. Rename `test_experiments.py` to `test_simulate.py`, keeping its tests and the fixture test from T003. Depends on T030, T033, T036, T037.

**Checkpoint**: `simulation/_legacy.py` is no longer used by any test except through `__init__`.

---

## Phase 6: User Story 4 - Code and diagrams say the same thing (Priority: P2)

**Goal**: the 4 diagrams that show experiments classes match the code (FR-007, research R7).

**Independent Test**: `uv run pytest tests/architecture/experiments_layout/test_diagrams_match_code.py`.

- [x] T039 [US4] Create `tests/architecture/experiments_layout/test_diagrams_match_code.py`, adapted from the mission one. For each of the 4 `.mmd` files, every experiments class shown has field names equal to its dataclass fields. `RunBaseline`, `ScriptedResponse`, `RunSnapshot`, `RescueScenario`, `CommunicationProfile`, `SimulationRun` and `SimulationResult` must appear in both `namespaces/Experiments` diagrams. Mark `xfail(strict=True, reason="until T042")`. Depends on T024.
- [x] T040 [P] [US4] Update `D/namespaces/Experiments/class-diagram.mmd` and `entity-relationship-diagram.mmd` to the field tables in `data-model.md`: add `RunBaseline`, `ScriptedResponse` and `RunSnapshot` with their relations (`RescueScenario *-- 1 RunBaseline`, `*-- 0..* ScriptedResponse`, `RunSnapshot *-- 1 SimulationRun`); `RescueScenario` gains `event_budget` and `communication_profiles`; `CommunicationProfile` gains `ship_id`; `SimulationRun` gains `scenario_id`, `scenario_revision`, `policy_id`, `policy_revision`, `result`. Regenerate both `.svg` files with `mmdc` 11.17.0 using the same flags as 004.
- [x] T041 [P] [US4] Apply the same experiments-class changes to `D/class-diagrams/scenario-model.mmd` and `D/entity-relationship-diagrams/scenario-model-er.mmd`, leaving every non-experiments part as it is; regenerate both `.svg` files.

---

## Phase 7: Polish & integration (serial)

- [x] T042 Point every package `__init__.py` at the new files; delete `models/_legacy.py`, `timeline/_legacy.py`, `results/_legacy.py` and `simulation/_legacy.py`; delete the emptied `tests/unit/experiments/models/test_experiment_models.py` and `tests/unit/experiments/results/test_results.py`; remove the `xfail` marks from T016, T017 and T039. Depends on T040 and T041 as well. Write the module docstring of `rescue/experiments/__init__.py`. Depends on T021, T024, T026, T027, T038, T040, T041.
- [x] T043 Edit `Makefile`: replace the `rescue/experiments` coverage line with `--include="rescue/experiments/models/*,rescue/experiments/timeline/*,rescue/experiments/results/*" --fail-under=100` and `--include="rescue/experiments/simulation/*" --fail-under=95`. Depends on T042.
- [x] T044 Edit `docs/planning/roadmap.md`: set 009 status to `Implemented`. Edit `docs/architecture/diagrams/rescue-domain-model/README.md` only if it lists the experiments classes. Depends on T043.
- [x] T045 Verify per `quickstart.md`: `make check-all` green; `Contracts: 13 kept, 0 broken.`; `grep -rn "rescue.bootstrap" rescue/experiments` empty; `test ! -e rescue/experiments/runner.py`; `uv run python -m rescue.demo | diff <scratchpad>/demo-before.txt -` empty; the T002 fixture tests pass. Record the results in the handoff. Depends on T044.

---

## Dependencies & Execution Order

```
T001 → T002 → US1 (T003 … T012) → T013 → T014 → T015 ─┬─ US2 classes (T018–T027)
                                                      ├─ US3 steps (T028–T038)
                                                      └─ US4 (T039 after T024; T040, T041 any time after T015)
                                    T016, T017 [P] after T014
US2 + US3 + US4 → T042 → T043 → T044 → T045
```

- US1 has no dependency on other stories and is the MVP.
- US2 and US3 both need T013–T015. US3's step tests import models through the package `__init__`, so they do not wait for US2's per-class files.
- US4 depends on US2's field layout only (T024).

## Parallel execution examples

- **US1**: after T005, run T008, T009 and T010 together (one file each). T004 runs alongside T003.
- **US2**: after T015, run T018, T019, T020, T022, T025 and T027 together; then T021, T023 and T026; then T024.
- **US3**: after T028, run T029, T035 and T037 together; then T031; then T032 and T033; then T034; then T036; then T038.
- **US4**: T040 and T041 together.
- US2, US3 and US4 can run at the same time; their files are disjoint.

## Implementation strategy

1. **MVP**: Setup + US1. The cycle is broken and the change is small and behaviour-neutral, so it can be reviewed and merged on its own.
2. **Increment 2**: US2. Files split, docstrings added, imports stable.
3. **Increment 3**: US3. Simulation steps.
4. **Increment 4**: US4. Diagrams.
5. Polish removes the `_legacy` scaffolding and tightens coverage gates.

## Notes

- Total: 45 tasks (T001–T045).
- `[P]` tasks: 22.
- Format check: every task has a checkbox, an ID, a story label in story phases, and at least one file path.
