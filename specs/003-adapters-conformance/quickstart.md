# Quickstart: Verify Adapters Conformance

Prerequisites: uv 0.13.8 and make (see `AGENTS.md` section 1).

| # | Command | Expected |
|---|---|---|
| 1 | `make install` | sync succeeds |
| 2 | `make check-all` | lint passes; `Contracts: 4 kept, 0 broken.`; all tests pass |
| 3 | the `== rescue/adapters` block of `make test` | `TOTAL ... 100%` (SC-003) |
| 4 | `uv run pytest tests/integration/adapters/contracts -v` | 9 tests pass, 3 of them seeded faults (SC-004) |
| 5 | `uv run python -m rescue.demo` | `rescue demo: confirmed=10, pending=0, status=complete; comparisons=3 scenarios x 2 policies`, the same as on `main` (SC-005) |
| 6 | temporarily add `import rescue.bootstrap` to `rescue/adapters/memory/clock.py`, then `uv run lint-imports`; revert | `adapters-inward ... BROKEN` (US4) |
| 7 | `grep -rn "class " rescue/bootstrap.py rescue/application/*.py` | no class implements a port (SC-001) |
| 8 | `grep -rn "\.snapshot()\|\.transact(" rescue --include=*.py` | every call is declared on `TransactionStore` (SC-002) |

The contracts are in [contracts/ports.md](contracts/ports.md); the shapes are in
[data-model.md](data-model.md).
