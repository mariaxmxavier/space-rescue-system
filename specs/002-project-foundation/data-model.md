# Data Model: Project Foundation

No runtime data. The entities are repository conventions.

## Check command

- **Name**: `make check-all`
- **Gates, in order**: format check → lint → import contracts → tests with coverage.
- **Result**: exit 0 only if every gate passes; the first failing gate's output names the tool and
  file. See [contracts/check-command.md](contracts/check-command.md).

## Import contract

- **Fields**: id, name, type (`forbidden`), source modules, forbidden modules,
  `allow_indirect_imports` (default false).
- **Rule**: every import-only assertion removed from `test_architecture.py` maps to one contract.
- **Lifecycle**: declared here (002) → tightened by package specs (003–010), e.g. 008/009 drop
  `allow_indirect_imports` on `application-no-memory`.
- See [contracts/import-contracts.md](contracts/import-contracts.md).

## Test location

- **Fields**: type, package, topic → path `tests/<type>/<package>/<topic>/test_<name>.py`.
- **type** ∈ {`unit`, `integration`, `e2e`, `architecture`}:

  | Type | Tests | Wiring |
  |---|---|---|
  | unit | one pure rule (models, pure functions, contracts) | none |
  | integration | parts wired through `new_run()` and the memory store | real in-memory adapters |
  | e2e | the whole system through its entry point (`run_demo`; HTTP API from 011) | full |
  | architecture | structure and boundaries of the code | none (static) |

- **package**: the `rescue` package under test (`mission`, `market`, `mobilisation`, `communication`,
  `experiments`, `application`, `adapters`, `values`), or the entry point for e2e (`demo`). The
  `architecture` type has no package level.
- **topic**: what is checked, named after the source module where one exists (`rules`, `policies`).
- **Invariant**: collected tests after the move = the 102 baseline (the two import-only tests are replaced by two contract tests, convergence T031).
- Mapping of existing files: spec FR-006.

## Doc location

- **kind** ∈ {`context`, `reference`, `architecture`, `planning`} → `docs/<kind>/…`; index at
  `docs/readme.md`.
- **Invariant**: every relative Markdown link outside `.specify/bridge-snapshots/` resolves.
