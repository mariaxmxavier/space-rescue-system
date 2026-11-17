# Quickstart: validate the foundation

## Prerequisites

- uv 0.13.8 (`uv --version`)
- make (Windows: `mise use -g make` or `winget install ezwinports.make`)
- Python 3.14.10 is fetched by uv from `.python-version`.

## Scenarios

| # | Do | Expect | Proves |
|---|---|---|---|
| 1 | Fresh clone; `make install` | uv resolves exact pins from `uv.lock` | US1-1, FR-001 |
| 2 | `make check-all` | pass; under 5 minutes including step 1 | US1-2, SC-001 |
| 3 | `uv run pytest --collect-only -q \| tail -1` | `102 tests collected` | SC-003 |
| 4 | `make test-unit`, `make test-integration`, `make test-e2e`, `make test-architecture` | each passes and runs only its folder | FR-005 |
| 5 | `find tests -name "test_*.py"` | every path matches `tests/<type>/<package>/<topic>/` (or `tests/architecture/<topic>/`) | SC-005 |
| 6 | Add `import rescue.adapters` to `rescue/mission/models.py`; `make check-all` | fails at `check-architecture`, names `domain-outward`; revert | US2-1, SC-004 |
| 7 | Repeat 6 with `import time` (→ `domain-io`) and `import rescue.adapters.memory` in `rescue/application/state.py` (→ `application-no-memory`) | each fails naming its contract; revert | SC-004 |
| 8 | Add an unformatted line; `make check-all` | fails at `lint`, names the file; revert | US1-3 |
| 9 | Link check over `*.md` (excluding `.specify/bridge-snapshots/`) | 0 missing relative targets | US3-4, SC-005 |
| 10 | `uv run python -m rescue.demo` | the demo prints its report as before | FR-011 |
| 11 | Push the branch / open the PR | `check` workflow passes | US4, SC-006 |

Command details: [contracts/check-command.md](contracts/check-command.md). Contract details:
[contracts/import-contracts.md](contracts/import-contracts.md).
