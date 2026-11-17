# Quickstart: Mobilisation Conformance

Prerequisites: [AGENTS.md](../../AGENTS.md) setup (uv 0.13.8, make).

```
make install
make check-all          # lint, contracts, full suite, per-package coverage
make compare            # comparison table: 5 algorithms × scenarios
make compare-trace      # same, plus JSON-lines trace of every algorithm step
```

Expected:

1. `check-all` passes; `rescue/mobilisation` shows 100% line and branch coverage.
2. `make compare` prints one row per algorithm per scenario with the columns in [contracts/allocator.md](contracts/allocator.md).
3. `make compare-trace` prints lines such as
   `{"algorithm": "earliest_arrival", "step": "pick", "ship_id": "ship-1", "detail": [["seats", "5"]]}` among the trace lines.
4. Demo output identical to `main`: `uv run python -m rescue.demo > after.txt` and diff with the output from `main`.
5. Seeded violations: adding `import rescue.mobilisation` in `rescue/mission/rules.py` makes `make check-architecture` fail.

## Baseline before implementation (2026-11-17)

- Worktree `006-mobilisation-conformance`: `250084db8bb76a1d1446026c736ed13e708a4817`.
- `main`: `a5746e11eeea257068d27aec2d8c48f58033a253`; merge base with this worktree: `250084db8bb76a1d1446026c736ed13e708a4817`.
- `uv --version`: 0.13.8; `.python-version`: 3.14.10. `make install` succeeded with the locked environment.
- `make check-all`: lint passed, all 3 existing import contracts passed, and 102 tests passed.
- Captured raw demo stdout (93 bytes) at `%TEMP%\space-rescue-006-demo-baseline.bin` for the post-change byte comparison. The command produced no stderr.
- The inherited `VIRTUAL_ENV` points at the neighbouring 005 worktree; uv warned and correctly used this worktree's `.venv`.

## Solver dependency setup (2026-11-17)

- Added and locked `ortools==9.15.6755` with uv 0.13.8. A fresh GIL-enabled environment selected from `.python-version` (`3.14.10+gil`) installed all 24 locked packages with `uv sync --locked`.
- Verified `ortools==9.15.6755` and imports of `SimpleMinCostFlow`, `CpModel`, `CpSolver` and `KnapsackSolver` on CPython 3.14.10 (`Py_GIL_DISABLED=0`). The official release provides the CPython 3.14 Windows x86-64 wheel; this machine's earlier free-threaded venv had no compatible Windows wheel, so `.python-version` now selects the cross-platform GIL build. See [research R7](research.md#r7-or-tools-version-and-apis).
- The original in-repository `.venv` remains in use by the editor's Python formatter and was not replaced. Setup and later checks use the fresh temp environment `%TEMP%\space-rescue-006-gil-default` to avoid interrupting that process.

## US1 checkpoint (2026-11-17)

- `uv run pytest tests/architecture/mobilisation -p no:cacheprovider -q`: 3 passed (diagram entity to file mapping, docstring presence, transient marking).
- `uv run pytest -p no:cacheprovider -q`: 155 passed (152 existing plus 3 new), 1131 subtests passed.
- `uv run ruff format --check` and `uv run ruff check` on `tests/architecture/mobilisation`: passed.
- Manual review: each entity module docstring covers what, when and why; `candidate.py` and `decision_context.py` say "transient".

## US2 checkpoint (2026-11-17)

- `uv run pytest tests/unit/mobilisation/services -p no:cacheprovider -q`: 56 passed (decision service, including the 10 characterisation tests migrated from the removed `policies` module).
- `uv run pytest tests/unit/mobilisation/models -p no:cacheprovider -q`: 110 passed.
- `uv run pytest tests/unit/mobilisation/algorithms -p no:cacheprovider -q`: 123 passed (allocator contract plus 8 greedy regression tests).
- `uv run pytest tests/architecture -p no:cacheprovider -q`: 12 passed, including one seeded violation per new contract in a temporary package.
- `uv run lint-imports` and `make check-architecture`: `Contracts: 7 kept, 0 broken.`
- `uv run pytest -p no:cacheprovider -q`: 396 passed, 1262 subtests passed.
- `uv run python -m rescue.demo > "$TEMP/space-rescue-006-demo-after.bin"` then `cmp` against the 93-byte baseline: identical (no output from cmp, exit 0).
- `rescue/mobilisation/policies.py` removed; `rescue/application/central.py` imports `select_offers` from `rescue.mobilisation.services.decide`.

## US3 checkpoint (2026-11-17)

- Machine: Windows 11, Python 3.14.10, uv 0.13.8, `make compare` and `uv run python -m benchmarks.mobilisation.compare`.
- Per-algorithm time on a five-ship scenario, from `runtime_ms` over 5 runs x 5 scenarios (25 samples each): earliest_arrival max 0.162 ms (mean 0.091); priority_queue max 0.167 ms (mean 0.077); min_cost_flow max 0.313 ms (mean 0.190); cp_sat max 12.692 ms (mean 7.570); knapsack max 0.182 ms (mean 0.134). Threshold < 1 s per algorithm: met (slowest sample 12.7 ms).
- Total comparison, wall clock of the whole entrypoint process (interpreter start, imports and 25 runs), 5 runs: 1.05, 0.90, 0.88, 0.92, 0.92 s. Threshold < 10 s: met.
- `uv run pytest tests/unit/mobilisation/services/test_compare.py tests/e2e/benchmarks tests/unit/mobilisation/algorithms -p no:cacheprovider -q`: 425 passed.
- `make compare` and `make compare-trace` exit 0; `make lint`: 91 files already formatted, all checks passed; `make check-architecture`: `Contracts: 7 kept, 0 broken.`
- Wall-clock thresholds are checked here only; no unit test asserts them.

## Acceptance (2026-11-17)

- `make install`: exit 0 with uv 0.13.8 and the locked environment. Run with `UV_PROJECT_ENVIRONMENT` pointed at the temp GIL environment, because the in-repository `.venv` is locked by the editor.
- `make check-all`: exit 0. Format check and ruff check pass; import contracts 7 kept, 0 broken; 702 tests passed (1647 subtests); `rescue/mobilisation`: 620 statements and 150 branches, 100% line and branch coverage (`--cov-fail-under=100`). These figures are after the final review's fix pass; the review found no Critical issue.
- `make compare`: exit 0, 25 rows (5 scenarios by 5 families). `make compare-trace`: exit 0, 280 JSON trace lines before the table.
- Demo: `uv run python -m rescue.demo` stdout is 93 bytes and byte-identical (`cmp`) to the T001 baseline captured at the merge base `250084d`. A fresh `main` checkout was not compared; `main` has moved past the merge base.
- Changes outside `rescue/mobilisation/`: `rescue/application/central.py`, one import line. The modules `models.py` and `policies.py` were replaced by packages and removed.
- Not done: no commits, pushes or pull requests, because the maintainer has not asked for them. The Codex job did not run (usage limit); the implementation was done by Claude subagents, and some documentation was finished by the orchestrator after the subagents hit the account limit.
- After merging `main` (777919b, which carries the mission and market conformance work): `make check-all` exit 0; 957 tests passed; import contracts 10 kept, 0 broken; demo output byte-identical to `main` (93 bytes), checked against a `git archive` snapshot of `main`.
- After merging `main` at `1e1d88d` (which adds the adapters conformance work): `make check-all` exit 0; 975 tests passed; import contracts 11 kept, 0 broken; demo output byte-identical to `main` (853 bytes), checked against a `git archive` snapshot of `main`.
