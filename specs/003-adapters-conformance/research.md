# Research: Adapters Conformance

No `NEEDS CLARIFICATION` remained after `/speckit-clarify`. Each decision below records what was
chosen, why, and what was rejected.

## R1 Ports as ABCs in `adapters/ports/`

- **Decision**: `TransactionStore`, `Clock` and `IdSource` are `abc.ABC` subclasses with
  `@abstractmethod`, one per file in `rescue/adapters/ports/`.
- **Rationale**: cosmic-python BP-ABC-INTERFACES puts abstract interfaces in `adapters/`. The
  2026-11-16 clarification chose option B. An ABC makes an adapter declare which port it
  implements, and an incomplete adapter fails at construction.
- **Alternatives**: `typing.Protocol` in `application/`, which was the original layout. It was
  rejected because the clarification chose ABCs and because a Protocol does not show which class
  implements which port.

## R2 `snapshot()` as a concrete template method on the port

- **Decision**: `TransactionStore.snapshot()` is concrete and implemented as
  `transact(lambda s: (s, s))`.
- **Rationale**: callers in `central.py` and `experiments/runner.py` already use it (FR-004).
  Building it on `transact` gives every store the same consistency for free, with no second
  abstract method to implement.
- **Alternatives**: an abstract `snapshot()`, rejected because every adapter would have to repeat
  the same line. Removing the callers' use of `snapshot()`, rejected because it touches
  application code, which belongs to spec 008.

## R3 Memory store commits optimistically (supersedes the single-lock decision)

- **Decision**: operations run in parallel on a snapshot with no lock held. The store publishes
  with a compare-and-swap on a version number, under a short guard lock. If another commit came
  first, the operation runs again on the newer state. A read-only operation publishes nothing.
- **Rationale**: the brief requires that requests and responses may occur in parallel
  (`docs/context/original-problem.md`, section 7). One lock around each whole operation serialises
  every request of a run. A per-mission lock is not enough, because `B3Market` holds span missions
  (constitution I). An actor queue also serialises everything. Optimistic commit keeps the
  `transact` port unchanged and keeps every operation correct by construction.
- **Consequences**: under contention, operations that conflict run again, so work is repeated and
  IDs drawn by a discarded attempt are never reused. Operations must therefore have no effect beyond
  drawing unique IDs. Sequential runs never conflict, so the demo output stays identical (FR-008).
- **Alternatives**: keep one lock (rejected: serialises the brief's parallel requests); per-mission
  locks (rejected: cross-mission market holds); a single-writer queue (rejected: serialises).

## R4 Contract checks as plain functions in the test tree

- **Decision**: each port gets a `check_<port>_contract(factory)` function that raises
  `AssertionError`, plus tests that run it against the memory adapter and against a deliberately
  broken adapter.
- **Rationale**: this proves the check catches a real fault (SC-004) with no new dependency. A
  plain function is simpler than a base `TestCase` mixin.
- **Alternatives**: a mixin test class, rejected as more code for the same result. Hypothesis
  property tests, rejected because they add a new dependency.
- **Known limit**: pytest runs with `--import-mode=importlib`, so another test file cannot import
  these checks without extra setup. A future adapter would move them into an importable helper
  module. No new adapter is planned.

## R5 Import contracts

- **Decision**: add `adapters-inward`, which forbids `adapters` from importing `bootstrap`,
  `demo`, `experiments`, `application.central`, `application.contracts` and the domain packages,
  with indirect imports allowed. Widen `application-no-memory` to cover `application`,
  `experiments` and `demo`. The `adapters-inward` contract enforces this denylist.
  `ArchitectureBoundaryTests.test_adapters_import_only_allowed_modules` enforces the allowlist
  with an AST check over every import in `rescue/adapters`.
- **Rationale**: these enforce US4. Indirect imports must be allowed because `application.state`
  imports `market` and `mission`. That is the temporary FR-010 exception, which 008 removes.
- **Alternatives**: a `layers` contract, rejected because the package is not layered yet (that is
  spec 010). A `ignore_imports` exception, rejected because the 002 architecture test forbids
  `ignore_imports`.

## R6 Documentation rule

- **Decision**: every module, class and public function in `rescue/adapters/` has a docstring
  covering what it does, when it is called and why it exists. It is checked in code review only,
  with no lint gate (clarification 2026-11-16).
- **Rationale**: the owner's request, recorded as repository rule P-0001.
- **Alternatives**: Ruff's pydocstyle `D` rules, which the owner declined.
