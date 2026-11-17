# Research: Project Foundation

Versions checked against PyPI and GitHub on 2026-11-16.

## R1 Toolchain and pins

- **Decision**: uv 0.13.8 manages the environment and `uv.lock`; Python 3.14.10 from
  `.python-version`. Dev group, exact pins: `ruff==0.17.5`, `pytest==9.2.0`, `pytest-cov==7.1.0`,
  `coverage==7.17.3`, `import-linter==2.16`. `[tool.uv] required-version = "==0.13.8"`.
- **Rationale**: the project-setup standard names these tools; all declare Python 3.14 support.
  No runtime dependencies are added.
- **Alternatives**: pip + requirements files (no lock of the interpreter); tox/nox (extra layer the
  standard rejects, D12).

## R2 Check command

- **Decision**: a root `Makefile` with `install`, `format`, `lint`, `check-architecture`, `test`,
  `test-unit`, `test-integration`, `test-e2e`, `test-architecture`, and `check-all` (the single
  check command). Every target is a `uv run …` line.
- **Rationale**: the project-setup standard (D12): CI calls make targets, the Makefile is the dev UX.
  CI runs on Linux where make exists.
- **Alternatives**: a Python `check.py` script (works without make on Windows, but departs from the
  standard and duplicates what make does); plain `uv run` lines in the README (no single command).
- **Consequence**: Windows contributors install make once (`mise use -g make` or
  `winget install ezwinports.make`); each target's `uv run` line also works by hand.

## R3 Tool configuration location

- **Decision**: all tool settings in `pyproject.toml` (`[tool.ruff]`, `[tool.pytest.ini_options]`,
  `[tool.coverage.*]`, `[tool.importlinter]`).
- **Rationale**: one file, fewer moving parts; every tool here reads `pyproject.toml`.
- **Alternatives**: one dedicated root file per tool (the standard's preference); rejected for this
  small repo to keep the foundation simple. A package spec may split a file out if it grows.

## R4 Lint rule set

- **Decision**: ruff `select = ["E4", "E7", "E9", "F", "I"]` (ruff defaults plus import sorting),
  `line-length = 100`, `target-version = "py314"`.
- **Rationale**: current code has 26 unsorted-import and 8 unused-import findings, all auto-fixable
  and behaviour-neutral (FR-012). Wider sets (SIM, UP, RUF, B) raise non-auto-fixable findings that
  would force real code edits; package specs 003–010 widen the set per package.
- **Check**: an unused import inside a package `__init__.py` may be a re-export; such cases get
  `__all__` instead of deletion.

## R5 Formatting

- **Decision**: `ruff format` is a gate. 32 of 46 files are reformatted once, in its own commit,
  before any file moves.
- **Rationale**: formatting is behaviour-neutral; a separate commit keeps the move diff readable.

## R6 Declared import contracts

Probed with import-linter 2.16 against current code:

| Contract | Type | Result today |
|---|---|---|
| Domain packages do not import `application`, `adapters`, `bootstrap` | forbidden | KEPT |
| Domain packages do not import I/O modules (`os`, `time`, `socket`, `urllib`, `http`, `subprocess`, `sqlite3`, `requests`, `httpx`, `sqlalchemy`) | forbidden, `include_external_packages = true` | KEPT |
| `application` does not import `adapters.memory` | forbidden | BROKEN indirectly: `application.central → experiments.runner → bootstrap → adapters.memory` |

- **Decision**: the third contract uses `allow_indirect_imports = true`, matching exactly what the
  hand-written test checks (direct imports only). Specs 008 and 009 break the cycle and remove that
  flag.
- **Domain packages** for both domain contracts: `rescue.mission`, `rescue.market`,
  `rescue.mobilisation`, `rescue.communication`, `rescue.experiments.models`,
  `rescue.experiments.results` (the last two from `test_experiment_models_and_results_remain_pure`).
- **What stays in `test_architecture.py`**: forbidden calls (`open`, `sleep`, `datetime.now`, …) and
  `os.environ` attribute reads. Its import-only assertions are removed once the contracts above pass
  and each one is shown to fail on a planted forbidden import (SC-004).
- **Note**: the declared domain contracts are stricter than the test (they also catch indirect
  imports); they pass today.

## R7 Test runner and layout

- **Decision**: pytest 9.2.0 runs the existing `unittest.TestCase` classes unchanged.
  `--import-mode=importlib`, `pythonpath = ["."]`, `testpaths = ["tests"]`, `--strict-markers`.
  `tests/__init__.py` is removed; no `__init__.py` in test folders.
- **Rationale**: importlib mode lets two folders hold files with the same base name (edge case in
  spec); `pythonpath` makes `rescue` importable without installing the project.
- **Running one type**: by path, `pytest tests/unit`. No markers are added; the folder is the type.
  (The standard's marker-by-path conftest is unnecessary while paths alone select a type.)
- **Path fix**: `test_architecture.py` locates the repo with `Path(__file__).parents[1]`; after the
  move to `tests/architecture/boundaries/` it becomes `parents[3]`. This is the only line changed in a
  moved test file, and no assertion changes.
- **Baseline**: `python -m unittest discover -s tests` runs **102 tests** today. Replacing the two
  wholly import-only architecture tests with contracts leaves 100; pytest must collect 100 before and
  after the move (SC-003).

## R8 Coverage per package

- **Decision**: `pytest --cov=rescue --cov-report=term-missing`; coverage lists each module under its
  package path (`rescue/mission/...`). No `fail_under` (FR-002).
- **Alternatives**: a custom per-package aggregation script; unnecessary until a package spec sets a
  minimum.

## R9 Automation

- **Decision**: `.github/workflows/check.yml` on `push` and `pull_request`, `ubuntu-24.04`,
  `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` (v7.0.1),
  `astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2` (v10.3.3) with `version: "0.13.8"`,
  then `uv python install` (reads `.python-version`), `make install`, `make check-all`.
- **Rationale**: actions pinned by commit SHA; the same uv, Python and command as locally. If 3.14.10
  is unavailable, `uv python install` fails and the job fails (edge case).

## R10 Canonical instructions

- **Decision**: `AGENTS.md` at the root is canonical; a root `CLAUDE.md` contains only `@AGENTS.md`.
- **Rationale**: one file for humans and all agents; Claude Code follows the import.

## R11 Docs layout

- **Decision**: `docs/diagrams/` → `docs/architecture/diagrams/`; `docs/roadmap.md` →
  `docs/planning/roadmap.md`; `context/` and `reference/` stay. Moves use `git mv` so history follows.
- **Links to update**: `docs/readme.md`; `specs/001-rescue-domain-model/spec.md` and `plan.md`;
  the render commands in the diagram README; `README.md` if it links docs. `.specify/bridge-snapshots/`
  are frozen and not edited.
- **Verification**: a link check over every `*.md` outside `.specify/bridge-snapshots/` finds 0
  missing relative targets (SC-005).
