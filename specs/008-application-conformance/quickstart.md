# Quickstart: Verify the Application Split

Use this to verify each wave and the finished feature. Contracts:
[public-api.md](contracts/public-api.md), [application-boundary.md](contracts/application-boundary.md).

## Prerequisites

- uv 0.13.8 and make (see [AGENTS.md](../../AGENTS.md) §1), then `make install`.
- The branch is rebased onto a `main` that contains 003 and 007 ([plan.md](plan.md), prerequisite
  gate). To check:

  ```
  git log --oneline main | grep -E "003|007"
  test -d rescue/adapters/ports && echo "003 present"
  ```

## 1. Capture the baseline (wave 0, before any code moves)

```
uv run python -m rescue.demo > "$SCRATCH/demo-before.txt"
make check-all 2>&1 | tail -n 40 > "$SCRATCH/check-before.txt"
git rev-parse HEAD > "$SCRATCH/base.txt"
```

`$SCRATCH` is any directory outside the repository. Expected: `make check-all` passes, and you
record the test count.

## 2. After every wave

```
make check-all
```

Expected: passes, and the test count is not lower than the baseline. A wave that only adds tests
increases it.

## 3. Final verification

| Check | Command | Expected | Covers |
|---|---|---|---|
| Behaviour and demo | `uv run python -m rescue.demo > "$SCRATCH/demo-after.txt"` then `cmp "$SCRATCH/demo-before.txt" "$SCRATCH/demo-after.txt"` | no output (byte-identical) | SC-005, FR-008 |
| Full gates | `make check-all` | passes | SC-005 |
| Coverage | `uv run coverage report --include="rescue/application/*" --fail-under=95` (also run by `make test`) | ≥95% line and branch | SC-004 |
| Boundaries | `make check-architecture` and `uv run pytest tests/architecture/boundaries` | 0 broken contracts, 0 cycles through application | SC-003 |
| Layout and docstrings | `uv run pytest tests/architecture/package_layout` | passes | SC-001, SC-002 |
| Service tests | `uv run pytest tests/unit/application/services` | passes; no test opens files, sockets or real clocks | Story 3.1 |
| Old modules gone | `test ! -e rescue/application/state.py && test ! -e rescue/application/contracts.py && test ! -e rescue/application/ports.py` | exit 0 | FR-002, FR-007 |
| No adapter → application edge | `grep -rn "rescue.application" rescue/adapters` | no output | SC-003, FR-007 |

## 4. Seeded violations (each must fail, then revert)

| Seed | Expected failure |
|---|---|
| add `from rescue.experiments.runner import simulate` inside any function in `rescue/application/` | the allowlist test and `application-inward` |
| add `from rescue.application.contracts import Result` to `rescue/adapters/memory/transaction_store.py` | the adapters allowlist test |
| pad one file in `rescue/application/services/` to 251 lines | `test_application_shape.py` |
| add a branch to one `RescueCentral` method body | `test_application_shape.py` |
| delete `Why:` from one private helper docstring | `test_docstrings.py` |
| rename a field of `RunState` without changing APP-ER | `test_diagrams_match_code.py` |

Revert every seed with `git checkout -- <file>` and rerun `make check-all`.
