# Working in this repository

This file is the one instruction source for humans and agents.

## 1. Setup

- Install uv 0.13.8 exactly. `pyproject.toml` sets `required-version = "==0.13.8"`, so any other uv refuses to run.
  - Windows PowerShell: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/0.13.8/install.ps1 | iex"`
  - macOS, Linux or Git Bash: `curl -LsSf https://astral.sh/uv/0.13.8/install.sh | sh`
  - Or `pip install uv==0.13.8`.
  - Confirm with `uv --version`; it must report 0.13.8.
- Python 3.14.10 needs no manual install. uv fetches it from `.python-version` during the first sync.
- On Windows, install make once: `mise use -g make` or `winget install ezwinports.make`.

## 2. Check command

Run once, then run the gates:

```
make install
make check-all
```

`make install` runs `uv sync --locked`. `make check-all` runs three gates in order and stops at the first failure:

- `lint`: `ruff format --check` and `ruff check` on `rescue` and `tests`.
- `check-architecture`: `lint-imports`, which enforces the contracts in section 3.
- `test`: pytest with a branch-coverage report for `rescue`, then a coverage report per package (`rescue/<package>`) and for the root modules.

Run one test type at a time with `make test-unit`, `make test-integration`, `make test-e2e` or `make test-architecture`. `make format` rewrites `rescue` and `tests` with ruff format.

## 3. Package layout

`rescue/` is the package, one folder per capability: `mission`, `market`, `mobilisation`, `communication`, `experiments`, `application` and `adapters`, plus the root modules `values.py`, `bootstrap.py` and `demo.py`.

Import rules live under `[tool.importlinter]` in `pyproject.toml`. Do not break them. The core four contracts (the full set of eleven is declared in `pyproject.toml` and checked by `make check-architecture`):

- `domain-outward`: domain packages (`mission`, `market`, `mobilisation`, `communication`, `experiments.models`, `experiments.results`) must not import `application`, `adapters` or `bootstrap`.
- `domain-io`: the same domain modules must not import `os`, `time`, `socket`, `urllib`, `http`, `subprocess`, `sqlite3`, `requests`, `httpx` or `sqlalchemy`.
- `application-no-memory`: only `bootstrap` imports `rescue.adapters.memory`; `application`, `experiments` and `demo` must not.
- `adapters-inward`: `adapters` imports only `rescue.application.state`, `rescue.values` and the standard library, enforced by import-linter and by an allowlist test over every import. Ports live in `rescue/adapters/ports/`, implementations in `rescue/adapters/memory/`, one class per file.

## 4. Test location

Put every test at `tests/<type>/<package>/<topic>/test_<name>.py`. Never add a test directly under `tests/`.

- `unit`: one pure rule, no wiring.
- `integration`: real parts wired through `new_run` and the memory store.
- `e2e`: the whole system through its entry point. The package level is the entry point, `demo` today.
- `architecture`: structure and boundary checks. It has no package level: `tests/architecture/<topic>/`.


## 5. Docs layout

- `docs/context/`: problem statement (`original-problem.md`).
- `docs/reference/`: glossary (`glossary.md`).
- `docs/architecture/`: diagrams (`diagrams/`) and decision records (`decisions/`).
- `docs/planning/`: roadmap (`roadmap.md`).

The index is `docs/readme.md`. Link every new document from it.

## 6. Roadmap

`docs/planning/roadmap.md` lists specs 002 to 013 with their dependencies, branches and status. Check a spec's dependencies there before you start it.

## 7. Spec workflow

1. `/speckit-specify`
2. `/speckit-clarify`
3. `/speckit-plan`
4. `/speckit-tasks`
5. Implementation through the superpowers bridge: `/speckit-superpowers-bridge` in Claude Code, `$speckit-superpowers-bridge` in Codex.

Spec artifacts live in `specs/<feature>/`.

## 8. Working rules

- Do not commit, push or open a pull request unless the maintainer asks.
- Do not edit `.specify/bridge-snapshots/`.
- Behaviour under `rescue/` must not change unless a task says so.
- **Rules:** this repository's rules for agents are in `docs/rules/`. At the start of an activity, load them with the rulebook skill; change them only through it, by pull request. Preferences and corrections go to the rulebook, never to the CLI's memory; project state goes to the spine and the repository's docs.
