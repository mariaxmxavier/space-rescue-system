---
description: "Tasks for 002 Project Foundation"
---

# Tasks: Project Foundation

**Input**: `specs/002-project-foundation/` — [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/),
[quickstart.md](quickstart.md)

**Tests**: no new test code is requested. Verification uses the existing suite, the check command,
and the plant-and-revert checks in [quickstart.md](quickstart.md).

**Rule for every task**: no behaviour change under `rescue/` (FR-012); `.specify/bridge-snapshots/`
is never edited; nothing is committed until the maintainer asks.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel with the other [P] tasks of the same phase (different files, no
  dependency on an unfinished task in that phase)
- **[Story]**: US1–US4 from spec.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: pinned toolchain and tool configuration (R1, R3, R4, R7, R8)

- [X] T001 Add to `pyproject.toml`: `[dependency-groups] dev = ["ruff==0.17.5", "pytest==9.2.0", "pytest-cov==7.1.0", "coverage==7.17.3", "import-linter==2.16"]`; `[tool.uv] required-version = "==0.13.8"`; `[tool.ruff] line-length = 100, target-version = "py314"`, `[tool.ruff.lint] select = ["E4", "E7", "E9", "F", "I"]`; `[tool.pytest.ini_options] testpaths = ["tests"], pythonpath = ["."], addopts = "--import-mode=importlib --strict-markers"`; `[tool.coverage.run] source = ["rescue"], branch = true`; `[tool.coverage.report] show_missing = true` (no `fail_under`)
- [X] T002 Run `uv lock` and `uv sync --locked` to create `uv.lock` and `.venv/`; confirm `uv run python --version` prints 3.14.10
- [X] T003 Confirm no `__pycache__` is tracked: `git ls-files | grep __pycache__` is empty; if not, `git rm -r --cached` those paths (`.gitignore` already ignores them)
- [X] T004 Record the baseline: `uv run pytest -q` collects and passes **102** tests (pytest runs the `unittest` classes unchanged; `tests/__init__.py` still present at this point); save `uv run python -m rescue.demo` output to the scratchpad as `demo-before.txt`

**Checkpoint**: tools installed at exact versions; 102 tests pass under pytest.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: one-time behaviour-neutral formatting and lint fixes, so every later gate starts green
(R4, R5). Touches almost every file, so it must finish before any move.

- [X] T005 Run `uv run ruff format rescue tests` (expected: 32 files reformatted)
- [X] T006 Run `uv run ruff check --fix rescue tests`; for any `F401` in a `rescue/**/__init__.py`, keep the name and add it to `__all__` instead of deleting it; fix any remaining finding by hand without changing behaviour
- [X] T007 Verify: `uv run ruff format --check rescue tests` and `uv run ruff check rescue tests` are clean; `uv run pytest -q` passes 102; `uv run python -m rescue.demo` output equals `demo-before.txt`

**Checkpoint**: format and lint clean, behaviour unchanged.

---

## Phase 3: User Story 1 - One command says whether the repository is healthy (P1) 🎯 MVP

**Goal**: `make check-all` gives one pass/fail across all gates.

**Independent test**: `make install && make check-all` passes; an unformatted line makes it fail at
`lint` naming the file.

- [X] T008 [US1] Create `Makefile` with targets exactly as in [contracts/check-command.md](contracts/check-command.md): `install`, `format`, `lint`, `check-architecture`, `test`, `test-unit`, `test-integration`, `test-e2e`, `test-architecture`, `check-all` (= `lint check-architecture test`); declare all as `.PHONY`. Contracts arrive in US2, so `make check-all` is first verified in T011; here verify with `make lint test`
- [X] T009 [US1] Verify US1 scenarios: `make install` then `make lint test` pass; add a badly formatted line to `rescue/values.py`, run `make lint`, see it fail naming the file, revert (quickstart 8)

**Checkpoint**: US1 delivered for format, lint and tests; the architecture gate joins in US2.

---

## Phase 4: User Story 2 - Package boundaries live in one declarations file (P1)

**Goal**: import rules declared in `pyproject.toml`, enforced by `make check-architecture`.

**Independent test**: each contract fails on a planted forbidden import and passes once reverted.

- [X] T010 [US2] Add `[tool.importlinter]` to `pyproject.toml`: `root_package = "rescue"`, `include_external_packages = true`, and the three contracts `domain-outward`, `domain-io`, `application-no-memory` exactly as tabled in [contracts/import-contracts.md](contracts/import-contracts.md) (`application-no-memory` with `allow_indirect_imports = true`)
- [X] T011 [US2] Run `make check-architecture`; all three contracts KEPT; then `make check-all` passes
- [X] T012 [US2] Plant-and-revert, one at a time (quickstart 6–7): `import rescue.adapters` in `rescue/mission/models.py` → fails `domain-outward`; `import time` in `rescue/market/models.py` → fails `domain-io`; `import rescue.adapters.memory` in `rescue/application/state.py` → fails `application-no-memory`. Revert each; `git diff rescue/` shows no planted line
- [X] T013 [US2] In `tests/test_architecture.py`: delete `test_domain_capabilities_do_not_import_application_adapters_or_bootstrap` and `test_experiment_models_and_results_remain_pure`; in `test_domain_capabilities_do_not_read_environment_or_use_io_clocks_or_network` delete the import loop (the `FORBIDDEN_IO_IMPORTS` and `FORBIDDEN_OUTER_IMPORTS` assertions), keeping the forbidden-call and `os.environ` checks; in `test_application_does_not_import_concrete_memory_adapter` keep only the `"MemoryTransactionStore" in names` check. Remove constants and helpers left unused (`FORBIDDEN_OUTER_IMPORTS`, `FORBIDDEN_IO_IMPORTS`, `_is_under` if unused). Run `make check-all`: passes with **100** tests

**Checkpoint**: US2 delivered; `make check-all` covers all four gates.

---

## Phase 5: User Story 3 - Tests and docs are easy to find (P1)

**Goal**: tests at `tests/<type>/<package>/<topic>/`, docs at `docs/<kind>/`, every link resolving.

**Independent test**: `make test-unit|test-integration|test-e2e|test-architecture` each pass and run
only their folder; total collected is 100; the link check finds 0 missing targets.

**Depends on**: T013 (edits `tests/test_architecture.py` before it moves).

### Tests move (four [P] tasks, one per type folder; each uses `git mv`)

- [X] T014 [P] [US3] Move unit tests: `tests/test_mission.py` → `tests/unit/mission/rules/`; `tests/test_market.py` → `tests/unit/market/rules/`; `tests/test_policies.py` → `tests/unit/mobilisation/policies/`; `tests/test_experiments.py` → `tests/unit/experiments/simulation/`; `tests/test_experiment_models.py` → `tests/unit/experiments/models/`; `tests/test_results.py` → `tests/unit/experiments/results/`; `tests/test_timeline.py` → `tests/unit/experiments/timeline/`; `tests/test_contracts.py` → `tests/unit/application/contracts/`; `tests/test_values.py` → `tests/unit/values/validation/`
- [X] T015 [P] [US3] Move integration tests: `tests/test_central.py` → `tests/integration/application/central/`; `tests/test_concurrency.py` → `tests/integration/application/concurrency/`; `tests/test_resilience.py` → `tests/integration/application/resilience/`; `tests/test_communication.py` → `tests/integration/application/communication/`; `tests/test_comparison.py` → `tests/integration/application/comparison/`; `tests/test_timing.py` → `tests/integration/application/timing/`; `tests/test_memory.py` → `tests/integration/adapters/memory/`
- [X] T016 [P] [US3] Move e2e test: `tests/test_demo.py` → `tests/e2e/demo/run/`
- [X] T017 [P] [US3] Move architecture test: `tests/test_architecture.py` → `tests/architecture/boundaries/`, and change `REPOSITORY_ROOT = Path(__file__).resolve().parents[1]` to `parents[3]` (the only edit)
- [X] T018 [US3] `git rm tests/__init__.py`; no `__init__.py` anywhere under `tests/`; run `uv run pytest --collect-only -q`: **100** collected; run `make test-unit`, `make test-integration`, `make test-e2e`, `make test-architecture`, each passes; `make check-all` passes (quickstart 3–5)

### Docs move

- [X] T019 [P] [US3] `git mv docs/diagrams docs/architecture/diagrams`; in `docs/architecture/diagrams/rescue-domain-model/README.md` replace `docs/diagrams/` with `docs/architecture/diagrams/` in the render commands, and add one `../` to every relative link that leaves the moved folder
- [X] T020 [P] [US3] `git mv docs/roadmap.md docs/planning/roadmap.md`; fix any relative link inside it
- [X] T021 [US3] Update links after T019–T020: `docs/readme.md` (diagrams → `architecture/diagrams/…`, add roadmap under a Planning heading), `specs/001-rescue-domain-model/spec.md` and `specs/001-rescue-domain-model/plan.md` (`../../docs/diagrams/` → `../../docs/architecture/diagrams/`), `specs/002-project-foundation/*.md` mentions of `docs/roadmap.md` → `docs/planning/roadmap.md`, and `README.md` if it links a moved file
- [X] T022 [US3] Link check: for every `*.md` outside `.specify/bridge-snapshots/` and `.venv/`, every relative link target exists — 0 missing (quickstart 9). A short throwaway script in the scratchpad is enough

**Checkpoint**: US3 delivered.

---

## Phase 6: User Story 4 - Every push is checked automatically (P2)

**Goal**: the same check runs on every push and pull request.

**Independent test**: push the branch; the `check` workflow passes.

- [X] T023 [P] [US4] Create `.github/workflows/check.yml`: `on: [push, pull_request]`; job `check` on `ubuntu-24.04`; steps `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` (v7.0.1), `astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2` (v10.3.3) with `version: "0.13.8"`, `uv python install`, `make install`, `make check-all`; `permissions: contents: read`
- [ ] T024 [US4] Verify after the maintainer approves a push: the workflow passes on the branch (SC-006). Not run without that approval

**Checkpoint**: US4 delivered.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T025 [P] Create `AGENTS.md`: setup (`uv`, make on Windows via `mise use -g make`), `make` targets, package layout, test location rule `tests/<type>/<package>/<topic>/` with the four type definitions from [data-model.md](data-model.md), docs kinds, roadmap link `docs/planning/roadmap.md`, spec workflow (`/speckit-specify → clarify → plan → tasks → implement`), no-commit-without-asking rule
- [X] T026 [P] Create `CLAUDE.md` containing only `@AGENTS.md`
- [X] T027 [P] Update `README.md` "Run it": `make install`, `make check-all`, per-type test targets, `uv run python -m rescue.demo`; keep the demo description (FR-011, constitution V)
- [X] T028 [P] Update `docs/planning/roadmap.md` row 002 status to `Implemented`
- [X] T029 Run every command in `AGENTS.md` and `README.md` as written; all succeed (FR-010); run quickstart scenarios 1–10 end to end; `git status` shows only intended changes

---

## Dependencies & Execution Order

```text
Setup (T001–T004) → Foundational (T005–T007) → US1 (T008–T009) → US2 (T010–T013)
                                                                      ↓
                                                     US3 tests (T014–T018), docs (T019–T022)
                                                                      ↓
                                                     US4 (T023–T024) → Polish (T025–T029)
```

- US1 before US2: the `check-architecture` target lives in the Makefile.
- US2 before US3: T013 edits `tests/test_architecture.py`, which T017 then moves.
- US3 docs (T019–T022) do not depend on US3 tests (T014–T018) and can run alongside them.
- US4 T023 only needs the Makefile (T008); it can be written any time after US1 but is verified last.
- Polish T028 needs T020 (roadmap moved).

## Parallel Examples

- **US3 tests**: T014, T015, T016, T017 together; each moves a disjoint set of files into its own
  type folder. Then T018.
- **US3 docs**: T019 and T020 together, also in parallel with T014–T017. Then T021, T022.
- **US4 + Polish**: T023, T025, T026, T027 together (four different new or edited files).

## Implementation Strategy

- **MVP**: Setup + Foundational + US1 (T001–T009): pinned tools and one command that checks
  format, lint and tests.
- **Then**: US2 (declared boundaries), US3 (layout), US4 (CI), Polish. After each phase `make
  check-all` passes, so work can stop at any checkpoint with a healthy repository.
- Suggested commits, when the maintainer asks: one per phase, with Foundational (formatting) on its
  own so the move diffs stay readable.

## Phase 8: Convergence

- [X] T030 Report coverage per `rescue` package in the `make test` output: add a total line for each package directory (mission, market, mobilisation, communication, experiments, application, adapters), with the root modules values.py, bootstrap.py and demo.py shown as their own line per FR-002 (partial)
- [X] T031 Restore the test count to 102: replace the two removed import-only architecture tests with two tests under `tests/architecture/boundaries/`: one runs `lint-imports` and asserts exit 0 with all three contracts kept; one reads `[tool.importlinter]` from pyproject.toml and asserts that domain-outward forbids `rescue.application`, `rescue.adapters` and `rescue.bootstrap`, and domain-io forbids every module in the removed FORBIDDEN_IO_IMPORTS set per SC-003 (partial)
