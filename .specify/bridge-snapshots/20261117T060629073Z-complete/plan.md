# Implementation Plan: Adapters Conformance

**Branch**: `003-adapters-conformance` | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-adapters-conformance/spec.md`

## Summary

Move the three ports (`TransactionStore`, `Clock`, `IdSource`) out of `rescue/application/ports.py`
into `rescue/adapters/ports/` as abstract base classes, one per file. Move their in-memory
implementations into `rescue/adapters/memory/`, one per file, each inheriting from its port.
Declare `snapshot()` on the store port. Add one reusable contract check per port, two import-linter
contracts, and what/when/why docstrings on everything in `rescue/adapters/`. `bootstrap.py` only
wires. Behaviour is unchanged. Details: [research.md](research.md); diagrams:
[design-diagrams.md](design-diagrams.md).

**Delivery status**: the code was written in the working tree on 2026-11-16, before this plan.
`make check-all` passes, and the demo output is byte-identical to `HEAD`. `/speckit-tasks` should
list each task, and the subagent-driven run re-verifies it and ticks it off rather than rewriting it.

## Technical Context

**Language/Version**: Python 3.14.10 (`.python-version`)

**Primary Dependencies**: none at runtime; standard library only (`abc`, `threading`, `decimal`).
Dev, exact pins from 002: uv 0.13.8, ruff 0.17.5, pytest 9.2.0, pytest-cov 7.1.0, coverage 7.17.3,
import-linter 2.16

**Storage**: in memory: one immutable `RunState` per run, versioned, with parallel operations and optimistic compare-and-swap commit (R3)

**Testing**: pytest, `unittest.TestCase` style; contract checks under
`tests/integration/adapters/contracts/` (R4)

**Target Platform**: developer laptops and GitHub Actions, through `make check-all`

**Project Type**: single Python package (`rescue/`)

**Performance Goals**: none new; the suite stays under 2 s

**Constraints**: no behaviour change (FR-008); demo output byte-identical; `adapters/` imports only
`rescue.application.state`, `rescue.values` and the standard library (FR-010, temporary until 008)

**Scale/Scope**: 9 source files in `rescue/adapters/`, 3 contract test files, 6 edited files
(`bootstrap.py`, `central.py`, `application/__init__.py`, `pyproject.toml`, `test_architecture.py`,
docs)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|---|---|---|
| I–II Seat accounting, final outcomes | No rule code changes; all existing tests keep their assertions | PASS |
| III Reliable operations | Store publishes by compare-and-swap on a version; a conflicting commit runs again on the newer state; the concurrent and parallel tests stay, and the contract check covers the no-publish-on-failure case | PASS |
| IV Simple design: rules separate from storage; abstractions need a documented need | Ports are the documented need (spec: Why); no new adapter types; `snapshot()` is a 1-line template method on the port, not a new layer | PASS |
| V Evidence | Contract check per port, each seeded with a broken adapter (SC-004); demo unchanged | PASS |
| Scope: exact versions | No new dependency | PASS |
| Workflow: spec → plan → tasks before implementation | Code exists ahead of plan (see Delivery status); tasks will re-verify it | PASS, with a recorded deviation |

Post-design re-check: PASS. No violations, so Complexity Tracking stays empty.

## Architecture (cosmic-python and clean architecture)

- **Layers**: ports and adapters sit in `adapters/`, which is the cosmic-python home for abstract
  interfaces (BP-ABC-INTERFACES). `application/` is the service layer and receives adapters by
  injection (BP-INJECT-ADAPTERS). `bootstrap.py` is the composition root, the only module that
  builds the memory adapters.
- **Dependency rule** (clean architecture): rules → nothing outward; application → ports;
  memory adapters → ports. No inner circle names an outer one. The one known exception is
  `adapters → application.state` (FR-010), which 008 removes.
- **Enforcement** (project-setup D7): import-linter contracts `adapters-inward` and
  `application-no-memory`, pinned in `test_architecture.py` so a contract cannot be loosened
  silently.

## Project Structure

### Documentation (this feature)

```text
specs/003-adapters-conformance/
├── spec.md
├── plan.md               # this file
├── research.md           # Phase 0: decisions R1–R6
├── data-model.md         # Phase 1: ports, adapters, invariants
├── contracts/ports.md    # Phase 1: behaviour every adapter must show
├── quickstart.md         # Phase 1: how to verify
├── design-diagrams.md    # Mermaid: dependencies, sequence, layout
├── checklists/requirements.md
└── tasks.md              # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
rescue/
├── adapters/
│   ├── __init__.py                 # why ports and adapters exist
│   ├── ports/
│   │   ├── __init__.py             # re-exports the three ports
│   │   ├── transaction_store.py    # TransactionStore(ABC): transact, snapshot
│   │   ├── clock.py                # Clock(ABC): now
│   │   └── id_source.py            # IdSource(ABC): next_id
│   └── memory/
│       ├── __init__.py             # re-exports the three adapters
│       ├── transaction_store.py    # MemoryTransactionStore
│       ├── clock.py                # ZeroClock
│       └── id_source.py            # SequenceIdSource
├── application/central.py          # imports ports from rescue.adapters.ports
└── bootstrap.py                    # wires memory adapters only

tests/
├── integration/adapters/
│   ├── memory/test_memory.py       # existing, unchanged
│   └── contracts/
│       ├── test_transaction_store_contract.py
│       ├── test_clock_contract.py
│       └── test_id_source_contract.py
└── architecture/boundaries/test_architecture.py   # 4 contracts pinned
```

**Structure Decision**: conform in place (roadmap rule), so no `models/services/entrypoints`
re-layout of other packages. Inside `adapters/`, the split is by role (`ports/` vs `memory/`),
then one class per file (repository rule P-0002).

## Parallel delivery (subagent-driven development)

Tasks are grouped in waves. `[P]` marks tasks whose write sets do not overlap, so their
implementers may be dispatched at the same time. Between waves the controller runs
`make check-all`. Each task gets a fresh implementer and then a task review covering spec
compliance and quality, per `superpowers:subagent-driven-development`. The final whole-branch
review runs on the most capable model.

| Wave | Tasks | Writes | Parallel | Depends on |
|---|---|---|---|---|
| 1 Ports | `ports/transaction_store.py`, `ports/clock.py`, `ports/id_source.py`, `ports/__init__.py` | `rescue/adapters/ports/` | [P] one per port file; `__init__` after | — |
| 2 Memory adapters | `memory/transaction_store.py`, `memory/clock.py`, `memory/id_source.py`, `memory/__init__.py`; delete `adapters/memory.py` | `rescue/adapters/memory/` | [P] one per adapter file; `__init__` after | Wave 1 |
| 3 Wiring | `bootstrap.py`, `central.py` import, `application/__init__.py`, delete `application/ports.py` | root and `application/` | sequential (one implementer) | Wave 2 |
| 4 Contract tests | three `test_*_contract.py` files | `tests/integration/adapters/contracts/` | [P] one per port | Wave 2 |
| 4 Import contracts | `pyproject.toml`, `test_architecture.py` | config and architecture test | [P] with the contract tests | Wave 3 |
| 5 Docs | `AGENTS.md`, `README.md`, `docs/planning/roadmap.md`, `docs/readme.md` | docs | [P] one per file | Wave 4 |
| 6 Gate | `make check-all`, demo byte-compare, seeded import violation | none | — | all |

**Ruling**: SDD's default is never to run implementers in parallel. Here a wave may run them in
parallel only when the tasks are marked `[P]` and touch disjoint files. Parallel reviewers are
always fine. If a parallel wave hits a merge conflict, it is re-run one task at a time.

**Models**: wave 1, wave 2, the contract tests and wave 5 are mechanical (one file each, with exact
content in the brief), so they use a cheap model. Wave 3 and the import contracts are cross-file
integration work, so they use a standard model. The final review uses the most capable model.

**How the run is driven**:
- **Input**: the plan file for the SDD scripts (`sdd-workspace`, `task-brief`, `review-package`)
  is `specs/003-adapters-conformance/tasks.md`, produced by `/speckit-tasks`. Its task IDs are the
  SDD task numbers.
- **Ledger**: `.superpowers/sdd/<plan>/progress.md` (git-ignored).
- **Agents**: implementers are the `implementer` agent; task reviewers are `code-reviewer`; the
  final whole-branch review is `code-reviewer` on the most capable model.
- **No commits**: implementers do not commit (repository rule: commit only when the maintainer
  asks). Review packages diff the working tree against the BASE commit instead.

## Complexity Tracking

Empty: no constitution violations.
