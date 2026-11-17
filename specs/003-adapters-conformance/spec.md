# Feature Specification: Adapters Conformance

**Feature Branch**: `003-adapters-conformance`
**Created**: 2026-11-16
**Status**: Draft
**Input**: "Bring `rescue/adapters/` up to the cosmic-python and clean-architecture rules. Keep it simple and direct: one class per file in nested folders, and every module, class and function says what it does, when it is called and why it exists."

## Why

The application needs three things from the outside world: a place to keep run state (`TransactionStore`), the current time (`Clock`) and fresh IDs (`IdSource`). These are **ports**. The code that provides them is an **adapter**.

Today the ports sit in `rescue/application/ports.py`, two adapters hide as private classes in `bootstrap.py`, and callers use `store.snapshot()`, which the port does not declare. A reader cannot find "where does time, ID or state come from" in one place, and a new store cannot replace the in-memory one.

## Target layout

```
rescue/adapters/
  ports/
    transaction_store.py   TransactionStore (abstract)
    clock.py               Clock (abstract)
    id_source.py           IdSource (abstract)
  memory/
    transaction_store.py   MemoryTransactionStore
    clock.py               ZeroClock
    id_source.py           SequenceIdSource
```

## User Stories

### US1 - One place for every port and adapter (P1)

A maintainer opens `rescue/adapters/` and finds every port and every implementation, one class per file. `bootstrap.py` only builds and wires them.

**Acceptance**:
1. Each port is an abstract class in `adapters/ports/`; each adapter inherits from its port and lives in `adapters/memory/`.
2. `bootstrap.py` and `application/` define no port or adapter; `application/ports.py` is gone.
3. The demo output and the full test suite are unchanged.

### US2 - Callers use only what the port declares (P1)

**Acceptance**:
1. `snapshot()` is declared on the `TransactionStore` port; every store operation used outside `adapters/` is declared there.
2. A snapshot read during a write returns the old or the new state in full, never a half-written one.

### US3 - Each port has a contract test (P2)

One reusable check per port runs against any implementation.

**Acceptance**:
1. Transaction store: success publishes the new state and returns the result; an exception or a non-`RunState` result publishes nothing.
2. ID source: repeated draws for one or more kinds never repeat within a run.
3. Clock: returns a valid instant; the zero clock always returns the same one.
4. Each check fails against a deliberately broken adapter.

### US4 - The boundary is enforced (P2)

`make check-all` fails when:
1. `adapters/` imports anything but `rescue.application.state`, `rescue.values` and the standard library.
2. `application/`, `experiments/` or `demo` import `rescue.adapters.memory`. Only `bootstrap` may.

### US5 - The code explains itself (P2)

Every module, class and public function in `adapters/` has a docstring that says **what** it does, **when** it is called and **why** it exists.

### Edge Cases

- A transaction raises after staging: nothing is published and the lock is released.
- A store built from something other than a `RunState` is rejected.
- IDs may repeat across separate runs; uniqueness is per run.
- A caller-supplied clock or ID source need not inherit from its port; any object with `now()` / `next_id()` is accepted, as today.

## Requirements

- **FR-001**: Ports are abstract base classes in `rescue/adapters/ports/`, one per file.
- **FR-002**: Adapters live in `rescue/adapters/memory/`, one per file, each inheriting from its port.
- **FR-003**: `bootstrap.py` only constructs and wires adapters.
- **FR-004**: `TransactionStore` declares every operation its callers use, including `snapshot()`.
- **FR-005**: Each port has one contract check that any adapter can run, and that fails on a broken adapter.
- **FR-006**: Import rules from US4 are declared import-linter contracts. The `adapters-inward` contract in `pyproject.toml` enforces the denylist. `ArchitectureBoundaryTests.test_adapters_import_only_allowed_modules` in `tests/architecture/boundaries/test_architecture.py` enforces the allowlist, with an AST check over every import in `rescue/adapters`. Both run in the build.
- **FR-007**: `rescue/adapters/` has 100% line and branch coverage.
- **FR-008**: Behaviour is unchanged: the full suite passes and the demo output is identical.
- **FR-009**: Every module, class and public function in `rescue/adapters/` has a what / when / why docstring. Other files this change touches (`bootstrap.py`, `central.py`) are out of scope; their own specs (008, 010) document them. Docstrings are checked in code review; no automatic gate.
- **FR-010**: Until spec 008 moves `RunState` inward, `adapters/` may import `rescue.application.state` (temporary exception).

## Success Criteria

- **SC-001**: 3 of 3 ports and 3 of 3 adapters live in `rescue/adapters/`; 0 in `bootstrap` or `application`.
- **SC-002**: 0 calls to store operations the port does not declare.
- **SC-003**: 100% coverage of `rescue/adapters/`.
- **SC-004**: 3 of 3 contract checks catch their seeded fault.
- **SC-005**: Full suite green; demo output byte-for-byte identical.

## Assumptions

- In-memory store, fixed clock and sequence IDs are enough; no new adapter types.
- The in-memory adapters double as test fakes.
- Other packages get the same treatment in their own specs (004–010); this spec touches only what moving the ports requires.
- `bootstrap.py` stays the composition root until spec 010.
- `docs/rules/`, the AGENTS.md "Rules" bullet and the `docs/readme.md` link record the maintainer's working rules (P-0001 docstrings, P-0002 one class per file). They are repository governance, adopted in the same working tree, not part of the adapters change, and are committed separately from it.

## Clarifications

### Session 2026-11-16

- Q: Ports as `Protocol`s in `application/`, or abstract classes in `adapters/`? → A: Abstract classes in `adapters/` (option B).
- Q: How is the code documented? → A: Docstrings saying what, when and why on every module, class and public function in `adapters/`.
- Q: Which code must carry what/when/why docstrings in this spec? → A: Only `rescue/adapters/`; touched files elsewhere wait for their own specs.
- Q: Should `make check-all` fail on a missing docstring in `rescue/adapters/`? → A: No; code review only.
- Q: Must a caller-supplied clock or ID source inherit from its port? → A: No; any object with the right method is accepted.
