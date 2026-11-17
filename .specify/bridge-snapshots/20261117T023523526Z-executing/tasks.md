# Tasks: Mission Conformance

**Input**: `plan.md`, `spec.md` (user stories US1–US4), `data-model.md`, `contracts/`, `research.md`, `quickstart.md`, `design-diagrams.md`

**Tests**: included. FR-007 and FR-009 require them, and the plan uses test-first delivery. Each model or rule task writes its test first (red), then the code (green).

**Organization**: by user story. Setup and Foundational come first and block everything. Phases 3–6 are independent once Foundational is done, except where a dependency is noted. Polish integrates and verifies.

## Format: `- [ ] TID [P?] [Story?] Description with path`

- **[P]**: different files, no dependency on an unfinished task. Dispatch these to parallel subagents together.
- **[Story]**: US1–US4, only in story phases.
- Every task names its owned files. Two `[P]` tasks never share a file (Constitution, Development Workflow).

## Path conventions

- Source: `rescue/mission/` (`P` = `rescue/mission/`)
- Unit tests: `tests/unit/mission/models/`, `tests/unit/mission/rules/`
- Architecture tests: `tests/architecture/mission_layout/`
- Diagrams: `docs/architecture/diagrams/rescue-domain-model/`

---

## Phase 1: Setup

**Purpose**: capture the baseline so later changes can be proven to change nothing.

- [ ] T001 Run `make install` then `make check-all` on the clean 004 checkout; record the result. Save the demo output with `uv run python -m rescue.demo > C:/Users/dudax/AppData/Local/Temp/claude/8c3396a68d4bcde5/489db567-fa4a-4e41-8923-d48d20816345/scratchpad/demo-before.txt`

---

## Phase 2: Foundational (blocks all user stories)

**Purpose**: move the old modules aside, add the closed vocabularies and shared private helpers, and put the import rules and architecture tests in place.

**Checkpoint**: `make check-all` is green with the new vocabularies, helpers and contracts. The architecture tests exist but are `xfail(strict=True)`.

- [ ] T002 `mkdir rescue/mission/models` then `git mv rescue/mission/models.py rescue/mission/models/_legacy.py`. Old code moves unchanged. Depends on T001.
- [ ] T003 `mkdir rescue/mission/rules` then `git mv rescue/mission/rules.py rescue/mission/rules/_legacy.py`. Depends on T002.
- [ ] T004 [P] Write `tests/unit/mission/models/test_request_outcome.py` first (red): 6 members (`PENDING`, `ACCEPTED`, `PARTIALLY_ACCEPTED`, `REFUSED`, `CANCELLED`, `EXPIRED`); `RequestOutcome("accepted") is RequestOutcome.ACCEPTED`; `RequestOutcome("acepted")` raises `ValueError`; `RequestOutcome.ACCEPTED == "accepted"`; `RequestOutcome.final()` returns the 5 non-pending members. Then create `rescue/mission/models/vocabulary/request_outcome.py` (`StrEnum`, docstring per contracts/docstring.md). Constraint: values exactly `pending, accepted, partially_accepted, refused, cancelled, expired`.
- [ ] T005 [P] Write `tests/unit/mission/models/test_progress_status.py` first (red), then `rescue/mission/models/vocabulary/progress_status.py` (`StrEnum`, docstring). Constraint: values exactly `complete, awaiting_responses, needs_more_help`; unknown value raises `ValueError`.
- [ ] T006 [P] Write `tests/unit/mission/models/test_history_action.py` first (red), then `rescue/mission/models/vocabulary/history_action.py` (`StrEnum`, docstring). Constraint: values exactly `request_created, accepted, partially_accepted, refused, cancelled, expired`.
- [ ] T007 [P] Create `rescue/mission/models/_validation.py` (private, docstrings with What and Why only). Move from `_legacy.py` these functions unchanged: `normalize_name`, `optional_id`, `optional_instant`, `signed_quantity`, and the Decimal-preserving `normalize_instant` wrapper. Keep every error message. Constraint: a `Decimal` input goes through `str()` before `values.normalize_instant`.
- [ ] T008 [P] Edit `pyproject.toml`: add the two contracts `mission-isolated` (forbidden) and `mission-layers` (layers) exactly as in `contracts/import-contracts.md`. Keep the existing `domain-outward`, `domain-io` and `application-no-memory` contracts.
- [ ] T009 [P] Edit `Makefile`: the `rescue/mission` coverage report line gains `--fail-under=100`.
- [ ] T010 [P] Create `tests/architecture/mission_layout/test_one_public_name_per_file.py`. It walks `rescue/mission/**/*.py` with `ast`: each non-`__init__`, non-underscore module defines exactly one public top-level class or function; `rescue.mission.models.__all__` and `rescue.mission.rules.__all__` equal the names in `contracts/public-imports.md`. Mark `@pytest.mark.xfail(strict=True, reason="until T045")`.
- [ ] T011 [P] Create `tests/architecture/mission_layout/test_docstrings.py`. Every module, class and public function in `rescue/mission/` has `What:`, `When called:`, `Why:`, `Diagram:`; private helpers need `What:` and `Why:`; every `Diagram:` path exists in the repo. Mark `xfail(strict=True, reason="until T045")`.
- [ ] T012 [P] Create `tests/architecture/mission_layout/test_diagrams_match_code.py`. Parse the 8 `.mmd` files (see `design-diagrams.md`, `data-model.md`). For each mission class shown, its field names equal the dataclass field names in code. Mark `xfail(strict=True, reason="until T034")`.
- [ ] T013 Write the re-export modules, all docstring-only except the re-exports: `rescue/mission/models/__init__.py` (exports the 9 names in `contracts/public-imports.md` from `_legacy` for the classes and from `vocabulary/` for the enums), `rescue/mission/models/vocabulary/__init__.py`, `rescue/mission/models/mission/__init__.py` and `rescue/mission/models/projections/__init__.py` (docstring only), `rescue/mission/rules/__init__.py` (exports the 5 rules from `_legacy`, `__all__` set). Depends on T002–T006.

---

## Phase 3: User Story 1 - Find and understand any mission part fast (Priority: P1) 🎯 MVP

**Goal**: each class and rule lives in its own file, under a folder that matches its diagram role, with the four-part docstring.

**Independent Test**: `uv run pytest tests/unit/mission/models tests/unit/mission/rules tests/architecture/mission_layout/test_one_public_name_per_file.py tests/architecture/mission_layout/test_docstrings.py` (the two architecture tests pass only after T045 and T047; before that the models and rules tests run on their own).

Each model task: write the test first, then the class, with its docstring per `contracts/docstring.md`. Field constraints are copied from `data-model.md`.

- [ ] T014 [P] [US1] Create `rescue/mission/models/mission/mission_data.py` (`MissionData`) and `tests/unit/mission/models/test_mission_data.py`. Constraints: `mission_id` non-blank Id; `station_name` non-blank str; `people_count` positive integer, fixed (`D`); `created_at` normalised Instant. Test that `Decimal("1.50")`, `"1.50"` and `1.50` normalise to the same instant (documents why the wrapper stays, research R3).
- [ ] T015 [P] [US1] Create `rescue/mission/models/mission/seat_request.py` (`SeatRequest`) and `tests/unit/mission/models/test_seat_request.py`. Constraints (verbatim from `data-model.md`): `requested_seats` > 0; `confirmed_seats` >= 0; `outcome` is `RequestOutcome`; `response_received_at` >= submitted and < deadline, `None` for cancelled and expired; `response_deadline` > submitted; `closed_at` >= submitted; `quote_id`, `revision_id`, `decision_id` are `Id | None`; ids `request_id`, `command_id`, `mission_id`, `ship_id` non-blank. Pending cannot confirm seats; accepted must confirm all requested.
- [ ] T016 [P] [US1] Create `rescue/mission/models/mission/request_history_entry.py` (`RequestHistoryEntry`) and `tests/unit/mission/models/test_request_history_entry.py`. Constraints: `mission_sequence` > 0; `action` is `HistoryAction`; `confirmed_seats_delta` and `pending_seats_delta` are integers (may be negative); `reason` non-blank; `message_id` `Id | None`.
- [ ] T017 [P] [US1] Create `rescue/mission/models/mission/mission.py` (`Mission`, the aggregate root) and `tests/unit/mission/models/test_mission.py`. Constraints: same identity rules as MissionData; `requests` and `history` are tuples; each request is a `SeatRequest`, each history entry a `RequestHistoryEntry`; mission owns history (not requests). Test that a non-tuple or wrong element type is rejected.
- [ ] T018 [P] [US1] Create `rescue/mission/models/projections/mission_progress.py` (`MissionProgress`) and `tests/unit/mission/models/test_mission_progress.py`. Constraints: `status` is `ProgressStatus`; `status` must equal the value derived from `C` and `P` (`complete` iff `C = D`; `awaiting_responses` iff `C + P = D`; else `needs_more_help`); `C + P <= D`; `unconfirmed = D - C`; `additional_needed = D - C - P`.
- [ ] T019 [P] [US1] Create `rescue/mission/models/projections/request_timing.py` (`RequestTiming`) and `tests/unit/mission/models/test_request_timing.py`. Constraints: a receipt time must not precede submission; with no receipt, elapsed is `None`; with a receipt, `waiting_seconds == 0` and elapsed equals receipt minus submission.
- [ ] T020 [US1] Create `rescue/mission/rules/_accounting.py` (private; What and Why docstrings) with `account(mission) -> (confirmed, pending)` and `append_history(...)`, moved from `_legacy.py`. Enforce `C >= 0`, `P >= 0`, `C + P <= D`. Depends on T014–T017.
- [ ] T021 [P] [US1] Create `rescue/mission/rules/register.py` (`register`) and `tests/unit/mission/rules/test_register.py`. Test: rejects a non-`MissionData` argument; returns a Mission with no requests and no history.
- [ ] T022 [P] [US1] Create `rescue/mission/rules/add_request.py` (`add_request`) and `tests/unit/mission/rules/test_add_request.py`. Test: each rejection (mismatched `mission_id`, non-pending request, submission time not equal to transition time, before mission creation, duplicate `request_id`, over remaining demand). Moved code keeps every error message.
- [ ] T023 [P] [US1] Create `rescue/mission/rules/apply_outcome.py` (`apply_outcome`) and `tests/unit/mission/rules/test_apply_outcome.py`. Test: each rejection (unknown request, closed request, non-final outcome, confirmation above requested, negative confirmation, accepted with partial, partial with 0 or full, refused with seats, before submission, at or after deadline). Accept `outcome` as `RequestOutcome` or its string value.
- [ ] T024 [P] [US1] Create `rescue/mission/rules/progress.py` (`progress`) and `tests/unit/mission/rules/test_progress.py`. Test: each of the three statuses; a read never changes the mission.
- [ ] T025 [P] [US1] Create `rescue/mission/rules/timing.py` (`timing`) and `tests/unit/mission/rules/test_timing.py`. Test: rejects a non-`SeatRequest`; rejects an observation time before submission; waiting and elapsed values for pending and answered requests.

---

## Phase 4: User Story 2 - Code and diagrams say the same thing (Priority: P1)

**Goal**: the mission parts of all 8 diagrams match the code (spec FR-004), and a test enforces it.

**Independent Test**: `uv run pytest tests/architecture/mission_layout/test_diagrams_match_code.py`.

Every diagram task: edit the mission parts only, keep non-mission parts unchanged, then render the `.svg` with `mmdc -i <mmd> -o <svg> -w 2400` (command list in the diagrams README, Source and rendering). Changes come from `data-model.md` "Diagram deltas".

- [ ] T026 [P] [US2] Edit `docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd` and re-render its `.svg`. Add: `SeatRequest` ids `mission_id`, `ship_id`, `quote_id`, `revision_id`, `decision_id`; `outcome` typed `RequestOutcome`; `Mission` owns `RequestHistoryEntry`; `MissionData`; `RequestTiming`; `<<enumeration>>` boxes for `RequestOutcome`, `ProgressStatus`, `HistoryAction`.
- [ ] T027 [P] [US2] Edit `.../namespaces/MissionOperations/entity-relationship-diagram.mmd` and re-render `.svg`. Add `message_id` to `RequestHistoryEntry`; add `ship_id`, `mission_id`, `quote_id`, `revision_id`, `decision_id` to `SeatRequest`; type `status` as `ProgressStatus`; ownership relation from `Mission` to history.
- [ ] T028 [P] [US2] Edit `.../namespaces/CoreReferences/class-diagram.mmd` and re-render `.svg`. Mission parts only, matching T026.
- [ ] T029 [P] [US2] Edit `.../namespaces/CoreReferences/entity-relationship-diagram.mmd` and re-render `.svg`. Mission parts only, matching T027.
- [ ] T030 [P] [US2] Edit `.../class-diagrams/domain-model.mmd` and re-render `.svg`. Mission parts only, matching T026.
- [ ] T031 [P] [US2] Edit `.../class-diagrams/scenario-model.mmd` and re-render `.svg`. Mission parts only, matching T026.
- [ ] T032 [P] [US2] Edit `.../entity-relationship-diagrams/domain-model-er.mmd` and re-render `.svg`. Mission parts only, matching T027.
- [ ] T033 [P] [US2] Edit `.../entity-relationship-diagrams/scenario-model-er.mmd` and re-render `.svg`. Mission parts only, matching T027.
- [ ] T034 [US2] Remove the `xfail` marker from `tests/architecture/mission_layout/test_diagrams_match_code.py` and run it green. Depends on T026–T033.

---

## Phase 5: User Story 3 - Seat rules are proven for every case (Priority: P2)

**Goal**: one test table applies every final outcome to every reachable request state and checks the seat invariants after each.

**Independent Test**: `uv run pytest tests/unit/mission/rules/test_invariant_table.py`.

- [ ] T035 [P] [US3] Create `tests/unit/mission/rules/test_invariant_table.py`. Parametrise over `RequestOutcome.final()` × reachable states (pending with 1, mid, all seats; each closed outcome). After each transition assert `C >= 0`, `P >= 0`, `C + P <= D`, and that a closed request is unchanged. Include the spec edge cases: partial acceptance with 0 confirmed behaves like refusal (releases the same seats, different outcome recorded); confirmation above requested is rejected and changes nothing; a repeated or out-of-order outcome on a closed request is rejected. Depends on T020, T022, T023.

---

## Phase 6: User Story 4 - Outcomes, statuses and history actions are named (Priority: P2)

**Goal**: callers outside `rescue/mission/` use the named values instead of string literals (FR-005, SC-004).

**Independent Test**: the grep in quickstart step 5 finds no mission literal in `rescue/`; the full suite stays green.

Every caller task swaps only mission literals (outcomes, statuses, history actions) for the enum member, and leaves market RFQ and quote literals (`pending`, `quoted`, `held`, `rejected`, `expired` on RFQs and quotes) alone (spec 005).

- [ ] T036 [P] [US4] `rescue/application/central.py`: swap mission outcome, status and action literals (about 20 sites) for `RequestOutcome`, `ProgressStatus` or `HistoryAction` members. Keep behaviour.
- [ ] T037 [P] [US4] `rescue/demo.py`: swap mission literals (about 8 sites). The demo output must not change (checked in T049).
- [ ] T038 [P] [US4] `rescue/experiments/models.py`: swap mission literals (about 3 sites).
- [ ] T039 [P] [US4] `rescue/experiments/results.py`: swap mission literals (about 2 sites).
- [ ] T040 [P] [US4] `rescue/experiments/runner.py`: swap mission literals (about 10 sites).
- [ ] T041 [P] [US4] `rescue/market/rules.py`: swap only the reads of `request.outcome` (lines near 85–87: `pending`, `accepted`, `partially_accepted`). Do not touch RFQ or quote statuses on lines 191–252.
- [ ] T042 [P] [US4] `rescue/application/contracts.py`: find mission literals; swap if any, otherwise change nothing and say so in the task report.
- [ ] T043 [P] [US4] `rescue/mobilisation/policies.py`: find mission literals; swap if any, otherwise change nothing and say so in the task report.

---

## Phase 7: Polish & integration (serial)

**Purpose**: switch the public imports to the new modules, delete the old ones, and verify everything.

- [ ] T044 Fold `tests/unit/mission/rules/test_mission.py` into the per-rule tests (T021–T025) and delete it. Every test in the old file must still exist somewhere under `tests/unit/mission/`. Depends on T021–T025.
- [ ] T045 Point `rescue/mission/models/__init__.py` and `rescue/mission/rules/__init__.py` at the new modules (not `_legacy`). Keep `__all__` exactly as in `contracts/public-imports.md`. Depends on T014–T025.
- [ ] T046 `git rm rescue/mission/models/_legacy.py rescue/mission/rules/_legacy.py`. Depends on T045.
- [ ] T047 Remove the `xfail` markers from `test_one_public_name_per_file.py` and `test_docstrings.py` and run them green. Depends on T045.
- [ ] T048 Run `make check-all`. It must pass, including `lint-imports` with both mission contracts and `rescue/mission` coverage at 100% line and branch. Depends on T035–T047.
- [ ] T049 Demo output unchanged: `uv run python -m rescue.demo > <scratchpad>/demo-after.txt`, then `diff` against `demo-before.txt` from T001. Must be identical. Depends on T048.
- [ ] T050 Boundary check: temporarily add `import rescue.market` to `rescue/mission/models/mission/mission.py`, run `make check-architecture`, confirm it fails naming `mission-isolated`, then revert and confirm green. Depends on T048.
- [ ] T051 Grep check from quickstart step 5. Record the output in the PR notes. Depends on T036–T043.

---

## Dependencies & Execution Order

### Phase dependencies

- **Setup (Phase 1)**: none.
- **Foundational (Phase 2)**: depends on Setup; blocks all user stories.
- **US1 (Phase 3)**: depends on Foundational. MVP.
- **US2 (Phase 4)**: depends on Foundational only (diagrams come from `data-model.md`); T034 also needs US1 code.
- **US3 (Phase 5)**: depends on T020, T022, T023 (US1 rules).
- **US4 (Phase 6)**: depends on T013 (re-exports include enums); independent of US1 code.
- **Polish (Phase 7)**: depends on all earlier phases.

### Story independence

- US1 is independently testable right after Foundational and T020–T025.
- US2 is independently testable after its eight diagram tasks.
- US3 needs US1 rules to exist, so it is not independent of US1.
- US4 needs only the enums, so it can run alongside US1.

## Parallel execution examples

Phase 2 fan-out (T004–T012, nine subagents):
```
Task: T004 request_outcome.py + test
Task: T005 progress_status.py + test
Task: T006 history_action.py + test
Task: T007 _validation.py
Task: T008 pyproject.toml contracts
Task: T009 Makefile coverage gate
Task: T010 architecture test: one public name per file
Task: T011 architecture test: docstrings
Task: T012 architecture test: diagrams match code
```

US1 models (T014–T019, six subagents), then T020 serially, then rules (T021–T025, five subagents).

US2 (T026–T033, eight subagents). Each owns one `.mmd` and its `.svg`.

US4 (T036–T043, eight subagents). Each owns one caller file.

## Implementation strategy

### MVP first (User Story 1 only)

1. Phase 1 → Phase 2 → Phase 3.
2. Stop and check: `make check-architecture`, the US1 tests, and the docstring and layout tests (T047).
3. Demo the layout: each class and rule has its own file.

### Incremental delivery

1. Foundation + US1 → layout and docstrings (MVP).
2. US2 → diagrams match code.
3. US3 → invariant table.
4. US4 → named values in callers.
5. Polish → full gates, byte-identical demo, boundary proof.

## Notes

- Format check: every task above has a checkbox, a TID, `[P]` only where the files are disjoint, a `[US#]` label only in story phases, and a file path.
- Change from the plan: the import contracts (T008) and coverage gate (T009) moved into Foundational, so every later wave is guarded from the start. The caller list is 8 files, not the 10 in the plan: `application/contracts.py` and `mobilisation/policies.py` are checked, and swapped only if they hold mission literals. `market/models.py` has no mission literals and is not on the list.
- Test literals in `tests/` are outside this task list. SC-004 says "outside `rescue/mission/`", which as written would include tests. Decide before PR whether to swap test literals too (it is a few dozen mechanical edits).
- Tests are never skipped: each xfail is removed in the phase that makes it pass (T034, T047).
