# Tasks: A Clear Application Layer

**Input**: Design documents from `specs/008-application-conformance/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/public-api.md](contracts/public-api.md),
[contracts/application-boundary.md](contracts/application-boundary.md),
[quickstart.md](quickstart.md), [design-diagrams.md](design-diagrams.md)

**Tests**: requested by the spec (FR-009: fake-port service tests, layout, docstring, diagram and
boundary checks; SC-004: 95% coverage). Write each test before the code it covers
(`superpowers:test-driven-development`).

**Organization**: one phase per user story. `[P]` means the task touches different files and does
not depend on an unfinished task, so it may go to a parallel subagent. Wave numbers refer to the
plan's "Parallel delivery" table.

**State on 2026-11-17 (revision 2, after 007 merged)**: 003 and 007 are on `origin/main`
(`ae38f1a`). The branch has no commits of its own, so it is already on `main`. Line ranges below
refer to `central.py` on `ae38f1a` and were measured that day. T001 re-checks them.

**Global constraints for every task**:
- Behaviour under `rescue/` does not change (FR-008). Move code verbatim. The allowed merge is
  `close_pending_request` (R8). Nothing else merges.
- One definition per file in `rescue/application/`. The only exception is `contracts/snapshots.py`,
  which holds 8 aliases (R7).
- Every new or moved module, class and function under `rescue/application/` and `rescue/state/`,
  private helpers included, has a docstring with `What:`, `When called:`, `Why:`, `Diagram:` in
  that order. `When called:` names the real callers. `Diagram:` gives an existing path, normally
  `docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd`
  (created by T003). No other code comments, except a one-line why for a non-obvious step.
- Services take ports keyword-only, typed by the ABCs in `rescue/adapters/ports/`, and never build
  adapters ([application-boundary.md](contracts/application-boundary.md)).
- `rescue/application/` never imports `rescue.adapters.memory`, `rescue.bootstrap`, `rescue.demo`
  or `rescue.experiments.{runner,simulator,timeline}`, not even inside a function.
- Tests live at `tests/<type>/<package>/<topic>/test_<name>.py` in `unittest.TestCase` style.
- No new dependency. Nobody commits (repository rule). Run `make check-all` at the end of every
  task.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup (wave 0)

- [x] T001 Prerequisite gate, passed 2026-11-17. `origin/main` (`ae38f1a`) contains 003 (`rescue/adapters/ports/` and `rescue/adapters/memory/`) and 007 (`rescue/communication/` with rules and models; `record_response` still in `central.py`, 269 lines). The branch had no commits, so the fast-forward was the rebase. Line ranges were re-measured and written into data-model.md §3–§4 and §6. Before dispatching wave 1, re-run the awk range check on `central.py`; if `main` moved, update the ranges
- [x] T002 Record the baseline. Write `git rev-parse HEAD` into `.superpowers/sdd/008-application-conformance/progress.md` as BASE. Run `make install`, save `uv run python -m rescue.demo` output to `<scratchpad>/demo-before.txt`, and save the tail of `make check-all` (test count, `rescue/application` coverage) to `<scratchpad>/check-before.txt`. If `make check-all` fails on `main` before any change, **stop and report `BLOCKED: main is red`**
- [x] T003 [P] Create the diagram skeletons so that every `Diagram:` path resolves from the first task onwards: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd (`classDiagram` with class `RescueCentral` only) and docs/architecture/diagrams/rescue-domain-model/namespaces/Application/entity-relationship-diagram.mmd (`erDiagram` with entity `RunState` and its fields from data-model.md §1, including `session_index`). Follow the style of namespaces/MissionOperations/*.mmd

---

## Phase 2: Foundational (waves 1a–1b; blocks every story)

- [x] T004 [P] Add `is_deeply_immutable(value: object) -> bool` to rescue/values.py with the exact body of `_deeply_immutable` in rescue/application/state.py (R6). True for `None`, exact `str`/`int`/`bool`/`bytes`, `Decimal`, `Enum`, tuples of immutables and frozen dataclasses of immutables; False otherwise. Write tests/unit/values/immutability/test_is_deeply_immutable.py first, covering each True case, a non-frozen dataclass, a frozen dataclass holding a list, a list, and a float. Then delete `_frozen_tree` from rescue/experiments/models.py and call `is_deeply_immutable` at its call sites. That also removes its function-local `dataclasses` import
- [x] T005 [P] Create the `Simulator(ABC)` port in rescue/adapters/ports/simulator.py with `@abstractmethod simulate(self, scenario: RescueScenario, policy: MobilisationPolicy, simulation_id: Id) -> RunSnapshot` (R4, data-model.md §5), and export it from rescue/adapters/ports/__init__.py. Docstring Why: "breaks the application → experiments.runner import cycle (FR-006)"
- [x] T006 Move `RunState` (depends on T004). Create rescue/state/run_state.py with the class body unchanged except that `_deeply_immutable` becomes `rescue.values.is_deeply_immutable`. Keep the `session_index: tuple[CommunicationSession, ...]` field added by 007 and its immutability check. Create rescue/state/__init__.py exporting `RunState` and delete rescue/application/state.py. Update every importer to `from rescue.state import RunState`: find them with `grep -rn "application.state" rescue tests`, which covers rescue/adapters/memory/transaction_store.py, rescue/adapters/ports/transaction_store.py, rescue/bootstrap.py, rescue/application/central.py and tests/integration/adapters/memory/test_memory.py. Write tests/unit/state/run_state/test_run_state.py for: a non-`B3Market` market is rejected; a non-`Mission` mission is rejected; duplicate `mission_id` is rejected with "mission IDs must be unique within a run"; a mutable value in any index (including `session_index`) is rejected; `mission()` returns the mission or `None`
- [x] T007 Update the adapters allowlist (depends on T005, T006). In tests/architecture/boundaries/test_architecture.py and the `adapters-inward` contract in pyproject.toml, remove `rescue.application.state`. Allow `rescue.state`, `rescue.values`, the domain model modules `rescue.experiments.models` and `rescue.mobilisation.models` (needed by the Simulator port, R4), and the standard library. `grep -rn "rescue.application" rescue/adapters` must print nothing
- [x] T008 [P] Write the shared test fakes in tests/unit/application/services/fakes.py (depends on T005, T006): `FakeStore(TransactionStore)` holding a `RunState`, where `transact` publishes only when the operation returns without raising and `snapshot` returns the current state; `FakeIds(IdSource)` returning `f"{kind}-{n}"` with a per-kind counter; `FakeSimulator(Simulator)` that records its calls and returns preset snapshots; `empty_state()` building `RunState("run-1", "central-1", B3Market("market-1"))`. Import them as `from tests.unit.application.services.fakes import ...` (pytest `pythonpath = ["."]`)

**Checkpoint**: `make check-all` passes, the demo output still equals the baseline, and no file under `rescue/adapters/` imports `rescue.application`.

---

## Phase 3: User Story 1 - Find one operation or type (Priority: P1) 🎯 MVP

**Goal**: each use case and application type has its own named file; Central only delegates (FR-001, FR-002, FR-005).

**Independent Test**: `uv run pytest tests/unit/application tests/integration/application` passes. Every row of data-model.md §2–§4 has a file. `RescueCentral` has no private method.

### Contracts split (wave 2)

- [x] T009 [P] [US1] Create rescue/application/contracts/result.py (`Result[T]`), result_status.py (`ResultStatus`), error_reason.py (`ErrorReason`, all 21 values) and snapshots.py (the 8 `*Snapshot` aliases from central.py lines 81–88), copied verbatim from rescue/application/contracts.py and central.py. Keep the `Result.__post_init__` rules: "`status` ∈ `ResultStatus`; `reason` ∈ `ErrorReason` or `None`"
- [x] T010 [P] [US1] Create the 16 command files under rescue/application/contracts/commands/ (register_mission.py … compare_policies.py, names from data-model.md §2, including `recover_reports.py` for `RecoverReports` at contracts.py line 148 and `synchronise_inbound.py` for `SynchroniseInbound` at line 165) plus commands/__init__.py. Each is `@dataclass(frozen=True, slots=True)` with "field order and defaults unchanged" from rescue/application/contracts.py
- [x] T011 [US1] Create rescue/application/contracts/__init__.py re-exporting every former name with an explicit `__all__`, then delete rescue/application/contracts.py (depends on T009, T010). tests/unit/application/contracts/test_contracts.py, rescue/demo.py, rescue/experiments/runner.py and the integration modules must pass **without edits** ([public-api.md](contracts/public-api.md))

### Shared helpers (wave 3)

- [x] T012 [US1] Create the 9 helpers in rescue/application/shared/, copied verbatim from central.py and renamed per data-model.md §4a: find_mission.py (`_mission`, 91–95), replace_mission.py (`_set_mission`, 96–106), find_session.py (`_session`, 107–113), replace_session.py (`_set_session`, 114–128), make_result.py (`_result`, 129–132), error_reason_for.py (`_reason`, 133–155), find_offer_revision.py (`_offer_revision`, 156–164), find_quote.py (211–214), find_rfq.py (215–218). Add shared/__init__.py with its docstring only. Do not delete the originals in central.py yet
- [x] T013 [US1] Create the remaining 6 helpers in rescue/application/shared/ (depends on T012): request_capacity_reason.py (`_request_capacity_reason`, 165–210), decision_link_reason.py (`_decision_link_reason`, 233–274), command_entry.py (`_command_entry`, 219–232), append_command.py (`_append_command`, 275–284), open_request.py (`_create_request`, 285–400, with the `central` parameter replaced by `id_source`), and close_pending_request.py (merges `_close_request` 731–764 with the `expire_request` body 696–730). `close_pending_request(state, mission_id, request_id, outcome, at, reason, *, id_source, guard=None)` order: unknown mission → unknown request → `ignored/closed_request` when not pending → inside `try`: `guard(request, instant)` may return a rejecting `Result` → `apply_outcome` → `applied` (R8). Write tests/unit/application/shared/close_pending_request/test_close_pending_request.py first: unknown mission, unknown request, closed request ignored, guard rejection publishes nothing, success, `DomainValidationError` mapped by `error_reason_for`

### Record-response delivery steps (wave 3b)

- [x] T014 [P] [US1] Create the five files in rescue/application/shared/delivery/ split from `record_response` (central.py 765–1033; data-model.md §4b): normalise_response.py, delivery_context.py (`DeliveryContext` frozen dataclass), classify_response.py, resolve_session.py and publish_delivery.py. `publish_delivery` is the nested closure turned into a module function, with the same arguments and the same index writes. Each file keeps the original logic verbatim. Write tests/unit/application/shared/delivery/ tests first for each step: receipt before send is rejected, a default `local:<ship>` session is created, `stale` returns `rejected/stale_session`, `duplicate` and `record` disposition paths, and that `publish_delivery` issues a report only for a received delivery with a session

### Services (wave 4; one implementer per folder, test first with T008 fakes)

Each test file covers every branch of its service: success, each rejection reason the code can
return, `replayed` where the service uses `command_entry`, `ignored` where it closes requests, and
"nothing published" on rejection. Each service file is at most 250 lines.

- [x] T015 [P] [US1] missions: rescue/application/services/missions/{register_mission,get_progress,get_history}.py from central.py 408–428, 1125–1137, 1138–1149; tests in tests/unit/application/services/missions/test_{register_mission,get_progress,get_history}.py
- [x] T016 [P] [US1] fleet: rescue/application/services/fleet/{register_ship,publish_availability,publish_offer}.py from central.py 429–441, 442–457, 458–498; tests in tests/unit/application/services/fleet/
- [x] T017 [P] [US1] quotes: rescue/application/services/quotes/{request_quotes,record_quote,accept_quote,reject_quote,expire_quotes}.py from central.py 499–547, 548–564, 565–625, 642–658, 659–686; `accept_quote` calls `shared.open_request`; tests in tests/unit/application/services/quotes/
- [x] T018 [P] [US1] requests (cancel_request calls close_pending_request with event_first=True; expire_request with event_first=False and its guard): rescue/application/services/requests/{create_request,cancel_request,expire_request}.py from central.py 626–641, 687–695, 696–730. `cancel_request` and `expire_request` both call `shared.close_pending_request`. `expire_request` passes a guard returning `rejected/invalid_input` when "request.response_deadline is None or instant < request.response_deadline". Tests in tests/unit/application/services/requests/
- [x] T019 [P] [US1] mobilisation: rescue/application/services/mobilisation/{mobilise,get_decision}.py from central.py 1250–1322 and 1150–1169; tests in tests/unit/application/services/mobilisation/
- [x] T020 [P] [US1] comparison: rescue/application/services/comparison/compare_policies.py from central.py 1187–1249. Replace the function-local `from rescue.experiments.runner import simulate` with the injected `simulator.simulate(scenario, policy, id_source.next_id("simulation"))`, and keep the snapshot read and the error mapping unchanged. The test uses `FakeSimulator` and asserts call order and `rejected/invalid_input` for an empty, duplicate or malformed `policy_keys`, an unknown scenario revision and an unknown policy revision
- [x] T021 [P] [US1] communication, record response: rescue/application/services/communication/record_response.py, the orchestrator that calls the T014 steps. Its four branches (duplicate, record, expire_then_record, apply_outcome) and the `id_source` event draws stay as in central.py 765–1033. Depends on T014. Tests in tests/unit/application/services/communication/test_record_response.py cover each branch with fakes, and the orchestrator stays under 250 lines
- [x] T022 [P] [US1] communication, other use cases: rescue/application/services/communication/{recover_reports,synchronise_inbound,get_session,get_deliveries}.py from central.py 1034–1071, 1072–1104, 1105–1124, 1170–1186. Each calls its communication rule of the same name, or the state lookup. Tests in tests/unit/application/services/communication/ with fakes for each one

### Facade and wiring (wave 5, sequential)

- [x] T023 [US1] Reduce rescue/application/central.py to the facade (depends on T011, T013–T022). Keep the frozen dataclass fields and add `simulator: Simulator` last. Each of the 22 public methods keeps its signature and becomes exactly `return <service>(..., store=self.store, ...)`. Delete every module-level helper, `_close_request` and the `TYPE_CHECKING` import of experiments. Import the aliases from `contracts.snapshots`
- [x] T024 [US1] Create rescue/experiments/simulator.py with `RunnerSimulator(Simulator)`, whose `simulate` does `from rescue.experiments.runner import simulate` inside the method and delegates (depends on T023). Docstring Why: "runner imports bootstrap at module level; the lazy import is temporary until 009 injects the run factory (R4)". In rescue/bootstrap.py, pass `simulator=RunnerSimulator()` to `RescueCentral(...)`. Fix any rescue/experiments/runner.py import that T006 or T011 broke
- [x] T025 [US1] Checkpoint: `make check-all` passes. `cmp <scratchpad>/demo-before.txt` against a fresh `uv run python -m rescue.demo` prints nothing. `test ! -e rescue/application/contracts.py && test ! -e rescue/application/state.py`

**Checkpoint**: US1 is complete and behaviour is unchanged. This is the MVP.

---

## Phase 4: User Story 2 - Understand the code and diagrams (Priority: P1)

**Goal**: four-part docstrings everywhere, plus UML and ER views that match the code (FR-003, FR-004).

**Independent Test**: `uv run pytest tests/architecture/package_layout` passes, and the diagram README renders both Application views.

- [x] T026 [P] [US2] Complete docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd: `RescueCentral <<facade>>`; one namespace per service folder with each service as a `<<use case>>` class (22 services); a `shared` namespace (15 helpers and the 5 delivery steps); `Result`, `ResultStatus`, `ErrorReason`, a `Commands` group listing the 16 commands; the 4 ports; `RunState`. Use dependency arrows only (R10)
- [x] T027 [P] [US2] Complete docs/architecture/diagrams/rescue-domain-model/namespaces/Application/entity-relationship-diagram.mmd: `RunState` with the fields from data-model.md §1, including `session_index`; `RunState ||--|| B3Market`, `RunState ||--o{ Mission`, `RunState ||--o{` each index, policies, scenarios and completed runs. No service entities (spec edge case)
- [x] T028 [US2] Render both views to `.svg` beside the sources with `mmdc` (as for the existing namespaces). Add an "Application" section with images and source links to docs/architecture/diagrams/rescue-domain-model/README.md (depends on T026, T027)
- [x] T029 [US2] Rename tests/architecture/mission_layout/ to tests/architecture/package_layout/ and parametrise test_docstrings.py and test_one_public_name_per_file.py over `("mission", "application")` (R9). Mission keeps its current label rules. For application, private definitions also need all four labels. Exempt only `rescue/application/contracts/snapshots.py` from one-public-name, with a reason string citing R7. The existing mission assertions must not weaken
- [x] T030 [US2] Extend tests/architecture/package_layout/test_diagrams_match_code.py with the two Application diagrams (depends on T026, T027, T029). Every class, enum and command under `rescue/application/contracts/` and every service function name appears in the class diagram. The `RunState` field names, including `session_index`, equal the ER entity fields
- [ ] T031 [US2] Create tests/architecture/package_layout/test_application_shape.py (depends on T029): (a) the AST of every public method of `RescueCentral` is one `Return` of a `Call`; (b) `RescueCentral` has no private methods; (c) every file under rescue/application/services/ is at most 250 lines; (d) every `.py` under rescue/application/ defines at most one public top-level name (contracts/__init__.py and snapshots.py excepted)
- [ ] T032 [US2] Docstring pass (depends on T029, T030): run `uv run pytest tests/architecture/package_layout` and fix every reported docstring in rescue/application/ and rescue/state/. Check that each `When called:` names real callers (`grep` them) and that each non-obvious constraint names its source (constitution principle, FR or R-number)

**Checkpoint**: US2 is complete. Every application file explains itself and points to a diagram that matches it.

---

## Phase 5: User Story 3 - Preserve boundaries and results (Priority: P1)

**Goal**: import boundaries enforced, no cycle through application, coverage gate, unchanged results (FR-006–FR-009).

**Independent Test**: `make check-architecture && uv run pytest tests/architecture/boundaries` passes, and each seeded violation in quickstart.md §4 fails.

- [x] T033 [P] [US3] Update the import contracts in pyproject.toml and tests/architecture/boundaries/test_architecture.py (R5). Replace `application-no-memory` with `application-inward` (forbidden: `rescue.adapters.memory`, `rescue.bootstrap`, `rescue.demo`, `rescue.experiments.runner`, `rescue.experiments.simulator`, `rescue.experiments.timeline`; no `allow_indirect_imports`). Add `state-inward` (source `rescue.state`; forbidden `rescue.application`, `rescue.adapters`, `rescue.bootstrap`, `rescue.demo`, `rescue.experiments`, `rescue.mobilisation`; **not** `rescue.communication`, because `RunState.session_index` holds its models). Add `rescue.state` to the `domain-io` sources. Update the reviewed contract table test. Add `test_application_imports_only_allowed_modules`, an AST walk over every `Import`/`ImportFrom` node in rescue/application/, function bodies included, against the allowlist in [application-boundary.md](contracts/application-boundary.md)
- [x] T034 [P] [US3] Create tests/architecture/boundaries/test_no_cycles.py. Build a grimp graph for `rescue` (`grimp.build_graph("rescue")`) and assert that `find_upstream_modules("rescue.application", as_package=True) & find_downstream_modules("rescue.application", as_package=True)` is empty; on failure, report the offending modules
- [ ] T035 [P] [US3] In Makefile, change the `rescue/application` coverage line to `--fail-under=95` and add an `== rescue/state` line with `uv run coverage report --include="rescue/state/*" --fail-under=100`. If application coverage is below 95%, add the missing branch tests under tests/unit/application/services/<folder>/
- [ ] T036 [US3] Run every seeded violation in quickstart.md §4 (depends on T031, T033–T035), confirm that each fails the named check, revert each with `git checkout -- <file>`, and record the six outcomes in the SDD ledger

**Checkpoint**: all three stories are complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T037 [P] Update docs: in AGENTS.md §3, add `state` to the package list, replace `application-no-memory` with `application-inward` and `state-inward`, and add the allowlist rule. Set 008 to "Implemented" in docs/planning/roadmap.md, and say that the remaining cycle edge is `experiments.simulator → runner → bootstrap`, owned by 009. Confirm that docs/readme.md links the spec and the diagram README
- [ ] T038 Final gate: `make check-all`; demo byte compare; the whole table in quickstart.md §3. Add a "Delivery status" paragraph to specs/008-application-conformance/plan.md with the test count before and after and the application coverage
- [ ] T039 Final whole-branch review: one `code-reviewer` agent on the most capable model, diffing against BASE from T002. Check the spec FRs and SCs, the constitution and [application-boundary.md](contracts/application-boundary.md). Fix the findings, or record why one is declined

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (T001–T003)**: T001 is done; T002 and T003 follow.
- **Foundational (T004–T008)**: after Setup; blocks all stories.
- **US1 (T009–T025)**: after Foundational. T014 needs T012; T021 needs T014; T023 needs T011 and T013–T022.
- **US2 (T026–T032)**: T026–T028 can start once T023 fixes the final names; T029–T032 after US1.
- **US3 (T033–T036)**: after US1. T036 also needs T031.
- **Polish (T037–T039)**: after all stories.

### User Story Dependencies

The stories are not independent, because this is a refactor of one module. US2 documents and US3
guards the files that US1 creates. Each story still ends at a passing `make check-all` checkpoint,
so delivery can stop after any story without leaving `main` broken.

### Within Each Phase

- Tests come before code (T004, T006, T013, T014, T015–T022).
- Contracts (T009–T011) come before shared helpers (T012–T013), which come before the delivery
  steps (T014), which come before the record-response orchestrator (T021), then the other services
  (T015–T022), then the facade (T023) and wiring (T024).
- Until T023, `central.py` stays untouched as the verbatim reference for T012–T022.

### Parallel Opportunities

| Wave | Parallel tasks | Disjoint write sets |
|---|---|---|
| 0 | T003 (after T002) | diagram skeletons |
| 1a | T004, T005 | values/experiments.models vs adapters/ports |
| 1b | T008 after T006 (T007 sequential) | tests fakes vs architecture test |
| 2 | T009, T010 | contracts core vs contracts/commands |
| 3 | T012 then T013 (sequential); T014 after T012 | shared lookups; shared/delivery |
| 4 | T015, T016, T017, T018, T019, T020 | one `services/<folder>/` plus its test folder each |
| 4b | T021 after T014; T022 with T021 | communication orchestrator vs the four other communication services |
| 6 | T033, T034, T035 | pyproject + test_architecture vs test_no_cycles vs Makefile |
| 7 | T026, T027 | class vs ER diagram |
| Polish | T037 | docs |

---

## Parallel Example: User Story 1, wave 4

```text
Controller dispatches implementers at once (cheap→standard model, plan "Models"):
  implementer A: T015 missions        writes services/missions/ + tests/.../services/missions/
  implementer B: T016 fleet           writes services/fleet/ + tests/.../services/fleet/
  implementer C: T017 quotes          writes services/quotes/ + tests/.../services/quotes/
  implementer D: T018 requests        writes services/requests/ + tests/.../services/requests/
  implementer E: T019 mobilisation    writes services/mobilisation/ + tests/.../services/mobilisation/
  implementer F: T020 comparison      writes services/comparison/ + tests/.../services/comparison/
  implementer G: T021 record response writes services/communication/record_response.py + its test
  implementer H: T022 other comm.     writes the four other services/communication/ files + tests
Then code-reviewer task reviews run in parallel; then `make check-all`; then T023.
```

---

## Implementation Strategy

### MVP first (US1)

1. T001 gate (done), then T002–T008.
2. T009–T025: the split, with behaviour unchanged and the demo byte-identical.
3. **Stop and validate** at T025. This is a mergeable state if needed.

### Incremental delivery

1. US1 gives navigable files.
2. US2 adds explanations and diagrams that match the code.
3. US3 adds the guards that keep the files that way.
4. Polish: docs, final gate and review.

### Subagent-driven execution

The after-tasks hook creates the Superpowers handoff, and `/speckit-superpowers-bridge` executes
it. The bridge uses a fresh `implementer` per task and a `code-reviewer` task review after each.
`[P]` tasks in one wave are dispatched together, and `make check-all` runs between waves. If a
parallel wave conflicts, it is re-run one task at a time. Nobody commits.

## Notes

- `[P]` = different files, no dependency on an unfinished task.
- Quote the data-model rules verbatim in briefs; do not paraphrase them.
- If `main` moves before wave 3, re-run the awk range check on `central.py` and update
  data-model.md §3–§4 before dispatching.
