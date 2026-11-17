# Contract: Make targets

Each target is one `uv run …` line, so it can also be typed by hand without make.

| Target | Runs | Fails when |
|---|---|---|
| `install` | `uv sync --locked` | lock out of date, wrong uv or Python |
| `format` | `uv run ruff format rescue tests` | never (rewrites files) |
| `lint` | `uv run ruff format --check rescue tests` then `uv run ruff check rescue tests` | unformatted file or lint finding |
| `check-architecture` | `uv run lint-imports` | a contract is broken |
| `test` | `uv run pytest --cov=rescue --cov-report=term-missing`, then one `uv run coverage report --include="rescue/<package>/*"` per package and one for the root modules | any test fails |
| `test-unit` | `uv run pytest tests/unit` | any unit test fails |
| `test-integration` | `uv run pytest tests/integration` | — |
| `test-e2e` | `uv run pytest tests/e2e` | — |
| `test-architecture` | `uv run pytest tests/architecture` | — |
| `check-all` | `lint`, `check-architecture`, `test` in that order | the first failing gate; exit code non-zero |

Output: each tool prints its own result; make stops at the first failure and prints the target
name, which identifies the gate (FR-002, US1 scenario 3).

Automation (`.github/workflows/check.yml`) runs `make install` then `make check-all` on every push
and pull request.
