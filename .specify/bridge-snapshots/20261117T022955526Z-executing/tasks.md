# Tasks: Adapters Conformance

**Input**: Design documents from `specs/003-adapters-conformance/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/ports.md](contracts/ports.md), [quickstart.md](quickstart.md)

**Tests**: requested by the spec (US3 contract checks, US4 architecture test, FR-007 100% coverage).

**Organization**: one phase per user story. `[P]` = different files, no dependency on an unfinished
task, so the task may be dispatched to a parallel subagent.

**State on 2026-11-16**: every file below already exists in the working tree, written before the
plan. Each implementer first compares the file with its task. If the file already matches, the
implementer runs the check, leaves the file as it is, and reports `DONE (verified)`. If it does
not match, the implementer fixes it. Nobody commits (repository rule).

**Global constraints for every task**:
- One class per file (rule P-0002).
- Every module, class and public function in `rescue/adapters/` has a docstring stating
  **What**, **When** and **Why** (rule P-0001, FR-009).
- No code comments.
- No change of behaviour under `rescue/` (FR-008).
- `rescue/adapters/` imports only `rescue.application.state`, `rescue.values` and the standard
  library (FR-010).
- Exact dependency versions; no new dependency.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [ ] T001 Record the baseline: write `git rev-parse HEAD` into the SDD ledger as BASE, run `make install`, and save the output of `uv run python -m rescue.demo`, run against a `git archive HEAD rescue` export, to `<scratchpad>/before.txt`

---

## Phase 2: Foundational (ports; blocks every story)

- [ ] T002 [P] Create the abstract `TransactionStore(ABC)` with `@abstractmethod transact(self, operation: Callable[[RunState], tuple[RunState, T]]) -> T` in rescue/adapters/ports/transaction_store.py. Invariant (data-model): "publishes only when `operation` returns `(RunState, result)` without raising".
- [ ] T003 [P] Create the abstract `Clock(ABC)` with `@abstractmethod now(self) -> Instant` in rescue/adapters/ports/clock.py. Invariant: "a finite, non-negative `Decimal`".
- [ ] T004 [P] Create the abstract `IdSource(ABC)` with `@abstractmethod next_id(self, kind: str) -> Id` in rescue/adapters/ports/id_source.py. Invariant: "never repeats within one run".
- [ ] T005 Re-export `Clock`, `IdSource` and `TransactionStore` with `__all__` and a what/when/why module docstring in rescue/adapters/ports/__init__.py; rewrite the package docstring in rescue/adapters/__init__.py to explain why ports and adapters exist (depends on T002–T004)

**Checkpoint**: `uv run python -c "import rescue.adapters.ports"` succeeds.

---

## Phase 3: User Story 1 - One place for every port and adapter (P1) 🎯 MVP

**Goal**: every port and adapter lives in `rescue/adapters/`, one class per file; `bootstrap.py` only wires.

**Independent Test**: `grep -rn "class " rescue/bootstrap.py rescue/application/` finds no port implementation; the demo output equals `before.txt`.

- [ ] T006 [P] [US1] Move `MemoryTransactionStore` unchanged into rescue/adapters/memory/transaction_store.py, inheriting from `TransactionStore`. Keep `TypeError("initial_state must be a RunState")` and `TypeError("transaction must return a RunState")`, and keep the single `threading.Lock`.
- [ ] T007 [P] [US1] Move bootstrap's `_ZeroClock` into rescue/adapters/memory/clock.py as the public `ZeroClock(Clock)`, which returns `Decimal("0")`.
- [ ] T008 [P] [US1] Move bootstrap's `_SequenceIdSource` into rescue/adapters/memory/id_source.py as the public `SequenceIdSource(IdSource)`. Keep the `reserved_ids` argument, the lock, `normalize_id(kind)` and the format `f"{normalized_kind}-{self._counter:08d}"`.
- [ ] T009 [US1] Re-export the three adapters with `__all__` in rescue/adapters/memory/__init__.py, then delete rescue/adapters/memory.py (depends on T006–T008)
- [ ] T010 [US1] In rescue/bootstrap.py, delete `_ZeroClock` and `_SequenceIdSource`. Import `MemoryTransactionStore`, `SequenceIdSource` and `ZeroClock` from `rescue.adapters.memory`, and `Clock`, `IdSource` and `TransactionStore` from `rescue.adapters.ports`. Drop the imports that are now unused (`Decimal`, `Lock`, `Instant`). (depends on T009)
- [ ] T011 [US1] In rescue/application/central.py, import the ports from `rescue.adapters.ports`. Update the docstring in rescue/application/__init__.py, then delete rescue/application/ports.py. (depends on T005)
- [ ] T012 [US1] Run `make check-all`, then compare the demo output with `<scratchpad>/before.txt` byte for byte (SC-005) (depends on T010, T011)

**Checkpoint**: US1 is complete; SC-001 and SC-005 hold.

---

## Phase 4: User Story 2 - Callers use only what the port declares (P1)

**Goal**: `snapshot()` is declared on the port.

**Independent Test**: `grep -rn "\.snapshot()\|\.transact(" rescue --include=*.py` lists only operations declared on `TransactionStore`.

- [ ] T013 [US2] Add the concrete `snapshot(self) -> RunState` to `TransactionStore`, implemented as `return self.transact(lambda state: (state, state))`, with a what/when/why docstring, in rescue/adapters/ports/transaction_store.py (research R2)
- [ ] T014 [US2] Confirm that rescue/application/central.py and rescue/experiments/runner.py call only `transact` and `snapshot` on the store, and that tests/integration/adapters/memory/test_memory.py (the concurrent-read test, contract TS-4) still passes unchanged (SC-002)

**Checkpoint**: SC-002 holds.

---

## Phase 5: User Story 3 - Each port has a contract test (P2)

**Goal**: one reusable check per port, each proven against a seeded broken adapter ([contracts/ports.md](contracts/ports.md)).

**Independent Test**: `uv run pytest tests/integration/adapters/contracts -v` gives 9 passed.

- [ ] T015 [P] [US3] Write `check_transaction_store_contract(make_store)` covering TS-1 to TS-3, with three tests in tests/integration/adapters/contracts/test_transaction_store_contract.py: it passes for the memory store; it raises `AssertionError` for a `PublishesOnException` store; and the memory store rejects a non-`RunState` initial state.
- [ ] T016 [P] [US3] Write `check_clock_contract(make_clock)` covering CL-1 ("finite `Decimal` ≥ 0"), with three tests in tests/integration/adapters/contracts/test_clock_contract.py: it passes for `ZeroClock`; it raises `AssertionError` for a `NegativeClock` that returns `-1`; and `ZeroClock` always returns `0` (CL-2).
- [ ] T017 [P] [US3] Write `check_id_source_contract(make_source)` covering ID-1 (150 draws across two kinds, no repeats), with three tests in tests/integration/adapters/contracts/test_id_source_contract.py: it passes for `SequenceIdSource`; it raises `AssertionError` for a `RepeatsIds` source; and a reserved ID is skipped (ID-2).

**Checkpoint**: SC-004 holds (3 of 3 seeded faults caught).

---

## Phase 6: User Story 4 - The boundary is enforced (P2)

**Goal**: import-linter fails when an adapter imports outwards, or when anything other than `bootstrap` imports the memory adapters.

**Independent Test**: quickstart step 6 (a seeded import is reported as `BROKEN`).

- [ ] T018 [US4] In pyproject.toml, widen `application-no-memory` to `source_modules = ["rescue.application", "rescue.experiments", "rescue.demo"]`. Add the `adapters-inward` contract: forbidden type; source `rescue.adapters`; forbidden `rescue.bootstrap`, `rescue.demo`, `rescue.experiments`, `rescue.application.central`, `rescue.application.contracts`, `rescue.mission`, `rescue.market`, `rescue.mobilisation`, `rescue.communication`; `allow_indirect_imports = true`. No `ignore_imports`. (research R5)
- [ ] T019 [US4] Pin both contracts in the expected table of `test_declared_import_contracts_match_the_reviewed_table`, and change the expected output to `"Contracts: 4 kept, 0 broken."`, in tests/architecture/boundaries/test_architecture.py (depends on T018)
- [ ] T020 [US4] Seed `import rescue.bootstrap` into rescue/adapters/memory/clock.py, check that `uv run lint-imports` reports `adapters-inward` as BROKEN, then revert the line and confirm `4 kept` (depends on T019)

**Checkpoint**: US4 holds.

---

## Phase 7: User Story 5 - The code explains itself (P2)

**Goal**: every module, class and public function in `rescue/adapters/` has a what/when/why docstring, checked by review only (clarification 2026-11-16).

**Independent Test**: a reviewer reads each file and finds **What**, **When** and **Why** in every docstring.

- [ ] T021 [P] [US5] Review and complete the docstrings in rescue/adapters/__init__.py and rescue/adapters/ports/*.py
- [ ] T022 [P] [US5] Review and complete the docstrings in rescue/adapters/memory/*.py

---

## Phase 8: Polish & Cross-Cutting

- [ ] T023 [P] In AGENTS.md section 3, list the four contracts and the `ports/` and `memory/` layout
- [ ] T024 [P] In README.md, describe the ports in `rescue/adapters/ports/` and the adapters in `rescue/adapters/memory/`
- [ ] T025 [P] Set 003 to `Implemented` in docs/planning/roadmap.md
- [ ] T026 [P] Link `docs/rules/` from docs/readme.md
- [ ] T027 Run quickstart steps 1–8: `make check-all` green, `rescue/adapters` at 100% (SC-003), 9 contract tests, demo identical (depends on all)

---

## Dependencies

```
T001 → T002,T003,T004 [P] → T005 → T006,T007,T008 [P] → T009 → T010 ┐
                              T005 → T011 ─────────────────────────────┴→ T012 (US1)
T002 → T013 → T014 (US2)
T009 → T015,T016,T017 [P] (US3)
T012 → T018 → T019 → T020 (US4)
T009 → T021,T022 [P] (US5)
all → T023–T026 [P] → T027
```

US2, US3 and US5 depend only on the foundational phase and the adapter files (T009); they do not depend on each other. US4 needs US1's wiring (T012).

## Parallel Execution Examples

- **Foundational**: dispatch T002, T003 and T004 to three implementers at once (three separate files).
- **US1**: dispatch T006, T007 and T008 together; T010 and T011 can then run as a pair, since they touch different files.
- **US3**: dispatch T015, T016 and T017 together.
- **After T012**: US3 (T015–T017), US5 (T021–T022) and the start of US4 (T018) touch disjoint files, so all six can run at once.
- **Polish**: dispatch T023 to T026 together.

## Implementation Strategy

1. **MVP = Setup + Foundational + US1 (T001–T012)**: the ports and adapters are in one place and the demo is unchanged.
2. Add US2, then the contract tests (US3), then the import contracts (US4), then the docstring review (US5). After each one, run `make check-all`.
3. Finish with the polish phase and quickstart (T027), then the final whole-branch review on the most capable model (plan: Parallel delivery).
