# Quickstart: verify Experiments Conformance

## Prerequisites

- uv 0.13.8. On Windows, if the first Python on PATH is free-threaded, set `UV_PYTHON` to a GIL
  CPython 3.14.10 build first (research R8).
- `make install`

## Baseline (on `main`, before any change)

```
uv run python -m rescue.demo > /tmp/demo-main.txt
uv run pytest tests/integration/application tests/unit/experiments -q
```

## Checks after the change

| Check | Command | Expect |
|-------|---------|--------|
| All gates | `make check-all` | green |
| Contracts | `make check-architecture` | `Contracts: 13 kept, 0 broken.` |
| No bootstrap import | `grep -rn "rescue.bootstrap" rescue/experiments` | no output |
| No runner left | `test ! -e rescue/experiments/runner.py` | true |
| Demo identical | `uv run python -m rescue.demo \| diff /tmp/demo-main.txt -` | no diff |
| Layout and docstrings | `uv run pytest tests/architecture/experiments_layout -q` | pass |
| Coverage | `uv run coverage report --include="rescue/experiments/simulation/*" --fail-under=95` after `make test` | pass; models, timeline and results at 100 |
| Function length | `tests/architecture/experiments_layout/test_one_public_name_per_file.py` (60-line check) | pass |

## Determinism

`tests/unit/experiments/simulation/test_simulate.py` runs a seeded scenario twice with
`start_run=new_run` and compares the result to a snapshot captured from `main` before wave 1.
