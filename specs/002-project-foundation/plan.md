# Implementation Plan: Project Foundation

**Branch**: `002-project-foundation` | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-project-foundation/spec.md`

## Summary

Pin the toolchain with uv, add one `make check-all` (ruff format and lint, import-linter contracts,
pytest with coverage), declare the import rules now hand-coded in `test_architecture.py`, move tests
to `tests/<type>/<package>/<topic>/` and docs to `docs/<kind>/`, run the same check in GitHub
Actions, and make `AGENTS.md` the one instructions file. Nothing under `rescue/` changes except
behaviour-neutral formatting and import fixes. Details: [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14.10 (`.python-version`)

**Primary Dependencies**: none at runtime. Dev, exact pins: uv 0.13.8, ruff 0.17.5, pytest 9.2.0,
pytest-cov 7.1.0, coverage 7.17.3, import-linter 2.16 (R1)

**Storage**: N/A

**Testing**: pytest 9.2.0 running the existing `unittest.TestCase` suites unchanged; baseline 102
tests (R7)

**Target Platform**: developer laptops (Windows, macOS, Linux) and GitHub Actions `ubuntu-24.04`

**Project Type**: single Python package (`rescue/`) with tests and docs

**Performance Goals**: install plus `make check-all` under 5 minutes (SC-001); suite runs in under 1 s
today

**Constraints**: exact versions everywhere; no `rescue/` behaviour change (FR-012); frozen
`.specify/bridge-snapshots/` untouched

**Scale/Scope**: 32 source files, 18 test files, about 30 doc files moved or relinked

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|---|---|---|
| I–III Seat accounting, outcomes, reliable operations | No rule code changes; all 102 tests that guard them keep running, assertions unchanged | PASS |
| IV Simple design: rules separate from storage, presentation and transport | Import contracts make the separation enforced, not just tested; tooling has a documented need (roadmap 003–010 report against it) | PASS |
| V Evidence: tests and demo; README explains how to run them | Demo command kept and checked (quickstart 10); README updated with the new commands (FR-011) | PASS |
| Scope: dependencies use exact versions | Every tool, action and the interpreter pinned exactly (R1, R9) | PASS |
| Workflow: spec → plan → tasks before implementation | This plan; tasks next | PASS |

Post-design re-check: PASS. No violations, so Complexity Tracking stays empty.

## Project Structure

### Documentation (this feature)

```text
specs/002-project-foundation/
├── spec.md
├── plan.md               # this file
├── research.md           # R1–R11 decisions
├── data-model.md         # check command, import contract, test and doc location
├── quickstart.md         # validation scenarios
├── contracts/
│   ├── check-command.md
│   └── import-contracts.md
└── checklists/requirements.md
```

### Source Code (repository root)

The package stays component-first, as the roadmap keeps it (each `rescue/<package>/` is a component;
cosmic-python layers inside components are the job of 003–010). Tests mirror it: test type first,
then component, then topic.

```text
AGENTS.md                         # canonical instructions (new)
CLAUDE.md                         # contains only @AGENTS.md (new)
Makefile                          # check targets (new)
pyproject.toml                    # + dev group, [tool.uv|ruff|pytest|coverage|importlinter]
uv.lock                           # (new)
.github/workflows/check.yml       # (new)
README.md                         # run instructions updated
rescue/                           # unchanged layout; formatting only
tests/
├── unit/
│   ├── mission/rules/test_mission.py
│   ├── market/rules/test_market.py
│   ├── mobilisation/policies/test_policies.py
│   ├── experiments/
│   │   ├── simulation/test_experiments.py
│   │   ├── models/test_experiment_models.py
│   │   ├── results/test_results.py
│   │   └── timeline/test_timeline.py
│   ├── application/contracts/test_contracts.py
│   └── values/validation/test_values.py
├── integration/
│   ├── application/
│   │   ├── central/test_central.py
│   │   ├── concurrency/test_concurrency.py
│   │   ├── resilience/test_resilience.py
│   │   ├── communication/test_communication.py
│   │   ├── comparison/test_comparison.py
│   │   └── timing/test_timing.py
│   └── adapters/memory/test_memory.py
├── e2e/
│   └── demo/run/test_demo.py
└── architecture/
    └── boundaries/test_architecture.py   # REPOSITORY_ROOT parents[1] → parents[3]
docs/
├── readme.md                     # index, links updated
├── context/original-problem.md
├── reference/glossary.md
├── architecture/diagrams/rescue-domain-model/…   # from docs/diagrams/
└── planning/roadmap.md           # from docs/roadmap.md
```

**Structure Decision**: the single-project layout above. `tests/__init__.py` is deleted; pytest runs
in importlib mode with `pythonpath = ["."]` (R7).

## Delivery order

Each step leaves `make check-all` green (the check-all gate exists from step 2 on).

1. **Toolchain**: dev group with pins, `uv lock`, `[tool.*]` config, Makefile. Tests still flat.
2. **Format and lint fixes**: `ruff format` and `ruff check --fix` on `rescue/` and `tests/`; 102
   tests pass; demo output unchanged. Own commit (R4, R5).
3. **Import contracts**: add the three contracts (R6); plant-and-revert each (SC-004); remove the
   import-only assertions from `test_architecture.py`, keeping the call and environment checks.
   Two methods are wholly import-only and are deleted
   (`…_do_not_import_application_adapters_or_bootstrap`, `…_models_and_results_remain_pure`), so
   the count goes 102 → 100 in step 3; convergence task T031 restores 102 with two contract tests (SC-003).
4. **Test move**: `git mv` per FR-006; delete `tests/__init__.py`; fix `REPOSITORY_ROOT`; collect
   count unchanged.
5. **Docs move**: `git mv` per R11; update links; link check is 0.
6. **CI**: `.github/workflows/check.yml` (R9).
7. **Instructions**: `AGENTS.md`, `CLAUDE.md`, README commands; roadmap row 002 status.

## Complexity Tracking

None.
