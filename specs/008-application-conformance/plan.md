# Implementation Plan: A Clear Application Layer

**Branch**: `008-application-conformance` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/008-application-conformance/spec.md`

## Summary

Split the 1322-line `rescue/application/central.py` into one service function per use case
(22 services in 7 responsibility folders) plus one file per shared orchestration helper.
`RescueCentral` keeps its 22 public methods; each becomes a one-line delegation. Split
`contracts.py` into a `contracts/` package with one file per command, result, enum and alias set.
Its `__init__` re-exports every name, so existing imports keep working. Move `RunState` to a new
inner package `rescue/state/`, and replace the two copies of the deep-immutability check with
one `is_deeply_immutable` in `rescue/values.py`. Inject simulation through a `Simulator` port, so
`application` no longer imports `experiments.runner`. Add the application UML and ER views, the
four-part docstrings, and checks for layout, docstrings, diagrams, central delegation, the import
allowlist, the absence of import cycles through `application`, and 95% coverage. Behaviour and demo
output stay unchanged. Decisions: [research.md](research.md). Types and file map:
[data-model.md](data-model.md). Diagrams: [design-diagrams.md](design-diagrams.md).

## Prerequisite gate (blocking implementation, not this plan)

The roadmap requires 003 and 007 to merge before 008 (both edit `central.py`). On 2026-11-17
neither has merged: 003 has uncommitted work in its worktree, and 007 has only its spec. This plan
targets `main` as it will be after both merge (R1):

- 003: ports are ABCs in `rescue/adapters/ports/`, memory adapters are in `rescue/adapters/memory/`,
  `snapshot()` is on the store port, and the `adapters-inward` contract and allowlist test exist.
- 007 (merged, PR #7): delivery classification moved into `rescue/communication/`. `record_response`
  (269 lines, still in `central.py`) is split by 008; see data-model §3 and §4.

Before `/speckit-tasks`, rebase onto `main` and check that both merged. Re-read `central.py` and
update the service-file table in [data-model.md](data-model.md) §3 if 007 changed the
`record_response` steps. If either has not merged, stop.

## Technical Context

**Language/Version**: Python 3.14.10 (`.python-version`)

**Primary Dependencies**: no runtime dependencies (standard library only). Dev pins from 002:
uv 0.13.8, ruff 0.17.5, pytest 9.2.0, pytest-cov 7.1.0, coverage 7.17.3, import-linter 2.16,
grimp 3.20 (installed with import-linter, used directly by the cycle test). No new dependency.

**Storage**: in memory: one immutable `RunState` per run behind the 003 `MemoryTransactionStore`

**Testing**: pytest, in `unittest.TestCase` style. New unit tests in
`tests/unit/application/services/<folder>/` use fake ports. The existing
`tests/integration/application/*` suites stay as the behavioural safety net, with their assertions
unchanged. Architecture tests go in `tests/architecture/`.

**Target Platform**: developer laptops and GitHub Actions, through `make check-all`

**Project Type**: single Python package (`rescue/`)

**Performance Goals**: none new; the suite stays at its current run time (±10%)

**Constraints**: no behaviour change (FR-008); demo output byte-identical to the pre-refactor
baseline (SC-005); no service module over 250 lines (SC-001); application coverage ≥95% line and
branch (SC-004); `application` imports only the allowlist in R5

**Scale/Scope**: about 65 new files under `rescue/application/` and 2 under `rescue/state/`.
Edited files: `central.py`, `adapters/ports/`, `adapters/memory/transaction_store.py`,
`bootstrap.py`, `values.py`, `experiments/models.py`, `experiments/runner.py` (imports only),
`pyproject.toml`, `Makefile`, tests and diagrams.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|---|---|---|
| I Safe seat accounting | No rule code changes; services call the same `mission_rules`/`market_rules`; capacity checks move verbatim into `shared/request_capacity_reason.py` | PASS |
| II Final request outcomes | `cancel_request` and `expire_request` share one `close_pending_request`, and the ignored-when-closed branch is kept; the existing timing and resilience suites run unchanged | PASS |
| III Reliable operations | Every mutating service runs its whole operation in one `store.transact`; replay via `command_entry` is kept; the concurrency suite runs unchanged | PASS |
| IV Simple design: abstractions need a documented need | One new port (`Simulator`) with a documented need (break the import cycle, FR-006); no repository, unit of work, message bus or service class hierarchy (R3) | PASS |
| V Evidence | Fake-port service tests for success, rejection and replay; demo byte compare | PASS |
| Scope: exact versions | No new dependency | PASS |
| Workflow: tasks name scope and dependencies; parallel writers own disjoint files | The wave table below assigns each `[P]` task its own files | PASS |
| Governance: deviations need approval | One temporary compromise: a function-local import in `experiments/simulator.py`, owned and removed by 009 (R4). It is outside `application`, so FR-006 holds | PASS, flagged for maintainer review |

Post-design re-check (after Phase 1): PASS. Complexity Tracking lists the one flagged compromise.

## Architecture (cosmic-python, clean architecture, project-setup)

- **Layers** (cosmic-python layer contract): `rescue/application/` is the **services** layer.
  Inside it, `services/` holds one function per use case, grouped by responsibility
  (`PR-COMPONENT-FIRST`, not `AP-PARALLEL-LAYOUTS`). `shared/` holds orchestration helpers used by
  two or more services, each with one implementation (FR-005). `contracts/` holds the plain
  request and response models that cross the use-case boundary (clean architecture: plain
  boundary data). `central.py` is a humble facade that only delegates.
- **Dependency rule**: `application → {domain packages, rescue.state, rescue.values,
  rescue.adapters.ports, stdlib}`. `adapters.memory → {adapters.ports, rescue.state,
  rescue.values}`. `rescue.state → {mission.models, market.models, values}`. Each port is defined
  once, in `adapters/ports/` (roadmap decision 003-B, `BP-ABC-INTERFACES`). Services receive ports
  as parameters (`BP-INJECT-ADAPTERS`) and never build a concrete adapter.
- **Composition root**: `bootstrap.new_run` builds the memory adapters and the `RunnerSimulator`,
  and passes them to `RescueCentral`. The facade passes only the ports each service needs
  (role-sized dependencies).
- **Validation**: services keep their current input normalisation, because it is the trust
  boundary for callers (`BP-VALIDATE-AT-BOUNDARY`). Domain rules keep their invariants.
- **Enforcement** (project-setup D7): import-linter contracts in `pyproject.toml`, an AST
  allowlist test that also catches function-local imports, a grimp cycle test, and layout tests.
  The coverage gate goes in the `Makefile`. All of these run in `make check-all`.

## Project Structure

### Documentation (this feature)

```text
specs/008-application-conformance/
├── spec.md
├── plan.md                         # this file
├── research.md                     # Phase 0: decisions R1–R10
├── data-model.md                   # Phase 1: types, service map, file → diagram map
├── contracts/
│   ├── public-api.md               # RescueCentral and import paths that must keep working
│   └── application-boundary.md     # service shape, ports, import allowlist, docstring rule
├── quickstart.md                   # Phase 1: how to verify
├── design-diagrams.md              # Mermaid: dependencies, sequence, layout, waves
├── checklists/requirements.md
└── tasks.md                        # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
rescue/
├── values.py                               # + is_deeply_immutable (one implementation)
├── state/
│   ├── __init__.py                         # re-exports RunState
│   └── run_state.py                        # RunState (moved from application/state.py)
├── adapters/
│   ├── ports/simulator.py                  # NEW Simulator(ABC): simulate(scenario, policy, id)
│   └── memory/transaction_store.py         # import RunState from rescue.state
├── experiments/
│   ├── models.py                           # _frozen_tree → values.is_deeply_immutable
│   ├── runner.py                           # import paths only
│   └── simulator.py                        # NEW RunnerSimulator(Simulator), lazy runner import (R4)
├── bootstrap.py                            # wires RunnerSimulator into RescueCentral
└── application/
    ├── __init__.py
    ├── central.py                          # RescueCentral facade: 22 one-line delegations
    ├── contracts/
    │   ├── __init__.py                     # re-exports every former contracts.py name
    │   ├── result.py  result_status.py  error_reason.py  snapshots.py
    │   └── commands/                       # 16 files, one per command (data-model §2)
    ├── shared/                             # 15 helper files + 5 delivery step files (data-model §4)
    └── services/
        ├── missions/       register_mission.py  get_progress.py  get_history.py
        ├── fleet/          register_ship.py  publish_availability.py  publish_offer.py
        ├── quotes/         request_quotes.py  record_quote.py  accept_quote.py
        │                   reject_quote.py  expire_quotes.py
        ├── requests/       create_request.py  cancel_request.py  expire_request.py
        ├── mobilisation/   mobilise.py  get_decision.py
        ├── communication/  record_response.py  recover_reports.py  synchronise_inbound.py
        │                   get_session.py  get_deliveries.py
        └── comparison/     compare_policies.py

tests/
├── unit/application/
│   ├── contracts/test_contracts.py         # existing; import unchanged
│   ├── services/<folder>/test_<service>.py # NEW: fake ports; success, rejection, replay
│   └── shared/<topic>/test_<helper>.py     # NEW only where a branch is not reached via services
├── unit/state/run_state/test_run_state.py  # NEW: validation moved with RunState
├── unit/values/immutability/test_is_deeply_immutable.py
├── integration/application/*               # existing; imports adjusted only
└── architecture/
    ├── boundaries/test_architecture.py     # + application allowlist, no adapter→application
    ├── boundaries/test_no_cycles.py        # NEW grimp: nothing application imports imports it back
    └── package_layout/                     # renamed from mission_layout, parametrised by package
        ├── test_docstrings.py              # mission + application (application: all 4 labels, private too)
        ├── test_one_public_name_per_file.py
        ├── test_diagrams_match_code.py     # + Application class/ER diagrams
        └── test_application_shape.py       # NEW: central delegates only; services ≤250 lines

docs/architecture/diagrams/rescue-domain-model/
├── README.md                               # + Application section linking both views
└── namespaces/Application/
    ├── class-diagram.mmd / .svg            # UML: facade, services, shared, ports, contracts
    └── entity-relationship-diagram.mmd / .svg   # ER: RunState and the indexes it owns
```

**Structure Decision**: keep everything in place, as the roadmap requires. `application/` is the
services layer of one component; inside it the code is grouped by responsibility, then one file
per definition (repository rule from 004). `rescue/state/` is a new inner package rather than a
module in `values.py`. `RunState` depends on mission and market models, and `values.py` must stay
free of domain imports (R2).

## Parallel delivery (subagent-driven development)

Tasks are grouped in waves. A `[P]` task has a write set that does not overlap any other `[P]`
task in its wave, so its implementer may run in parallel. The controller runs `make check-all`
between waves. Each task gets a fresh `implementer` and then one `code-reviewer` task review
(spec compliance plus quality), per `superpowers:subagent-driven-development`. The final
whole-branch review uses the most capable model.

| Wave | Tasks | Writes | Parallel | Depends on |
|---|---|---|---|---|
| 0 Baseline | rebase gate (above); capture demo baseline to scratch; record test count and coverage | none in repo | — | 003, 007 merged |
| 1a Inner values | (a) `values.is_deeply_immutable` + test, swap `experiments/models._frozen_tree`; (c) `adapters/ports/simulator.py` | (a) `values.py`, `experiments/models.py`, `tests/unit/values/immutability/`; (c) `adapters/ports/simulator.py`, `adapters/ports/__init__.py` | [P] a, c | 0 |
| 1b Run state | (b) `rescue/state/` + test using `is_deeply_immutable`; delete `application/state.py`; fix its importers | `rescue/state/`, `adapters/memory/transaction_store.py`, `bootstrap.py` import line, `application/central.py` import line, `tests/unit/state/`, `tests/integration/adapters/memory/` | sequential | 1a |
| 2 Contracts split | `contracts/` package: 4 core files + 16 command files + `__init__`; delete `contracts.py` | `rescue/application/contracts/` | [P] one implementer for core + `__init__`, one for `commands/` | 1b |
| 3 Shared helpers | 15 helper files and 5 delivery step files in `application/shared/` copied verbatim from `central.py` privates (data-model §4), with docstrings | `rescue/application/shared/` | [P] split into 3 batches by file (lookups / request guards / transitions) | 2 |
| 4 Services | 22 service files + unit tests with fake ports; `record_response` is split (data-model §3) | `services/<folder>/` and `tests/unit/application/services/<folder>/` | [P] one implementer per folder (7) | 3 |
| 5 Facade and wiring | `central.py` reduced to delegations; `RescueCentral.simulator` field; `experiments/simulator.py`; `bootstrap.py` wiring; `experiments/runner.py` imports | `central.py`, `bootstrap.py`, `experiments/` | sequential (one implementer) | 4 |
| 6 Checks | (a) import contracts + allowlist + no-cycle test; (b) `package_layout/` rename and parametrise + `test_application_shape.py`; (c) `Makefile` coverage ≥95 for application and a `rescue/state` line | (a) `pyproject.toml`, `tests/architecture/boundaries/`; (b) `tests/architecture/package_layout/`; (c) `Makefile` | [P] a, b, c | 5 |
| 7 Diagrams and docs | (a) Application class + ER `.mmd`/`.svg`; (b) diagram README section + `docs/readme.md` link + roadmap status; (c) docstring `Diagram:` paths sweep | (a) `namespaces/Application/`; (b) docs; (c) `rescue/application/**` docstrings only | (a) [P] with (b); (c) after (a) | 6 (diagram test from 6b must exist first) |
| 8 Gate | `make check-all`; demo byte compare; seeded violations (function-local runner import, adapter→application import, 251-line service) each fail | none | — | all |

**Ruling**: the SDD default is never to run implementers in parallel. A wave may run them in
parallel only when its tasks are marked `[P]` and touch disjoint files. Parallel reviewers are
always fine. Waves 3 and 4 both read `central.py` but do not write it, and only wave 5 changes it,
so the old code stays as the reference until the facade is cut over. If a parallel wave hits a
conflict, it is re-run one task at a time.

**Models**: waves 2, 3 and 7c are mechanical moves with exact source line ranges in the brief, so
they use a cheap model. Waves 1, 4, 5 and 6 need judgement (fakes, wiring, contracts), so they use
a standard model. Task reviews use the standard model. The final whole-branch review uses the most
capable model.

**How the run is driven**:
- **Input**: `specs/008-application-conformance/tasks.md` from `/speckit-tasks`; its task IDs are
  the SDD task numbers. The after-tasks hook creates the Superpowers handoff, and
  `/speckit-superpowers-bridge` executes it.
- **Ledger**: `.superpowers/sdd/<plan>/progress.md` (git-ignored).
- **Agents**: implementers are the `implementer` agent, task reviewers are `code-reviewer`, and
  the final review is `code-reviewer` on the most capable model.
- **No commits**: implementers do not commit (repository rule). Review packages diff the working
  tree against the BASE commit recorded in wave 0.
- **Brief rule for waves 3 and 4**: move the code verbatim. A behavioural edit is allowed only
  where a shared helper replaces a duplicate (`close_pending_request`), and it must be named in the
  brief.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Function-local `from rescue.experiments.runner import simulate` inside `experiments/simulator.py` (temporary, until 009) | `runner` imports `bootstrap` at module level, so a top-level import from the composition root would fail at import time | Keeping the import in `application` breaks FR-006. Injecting the run factory into `runner` now is 009's scope, and doing it here would widen 008 into the experiments package |
