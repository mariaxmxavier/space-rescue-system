# Research: A Clear Application Layer

Phase 0 for [plan.md](plan.md). Each entry gives the decision, the rationale and the alternatives
considered. No `NEEDS CLARIFICATION` remains.

## R1. Baseline: plan against `main` after 003 and 007

- **Decision**: design against `main` after 003 (ports as ABCs in `rescue/adapters/ports/`, memory
  adapters in `rescue/adapters/memory/`, `snapshot()` declared on the store port) and 007 (delivery
  classification extracted from `record_response`). Implementation starts only after rebasing onto
  a `main` that contains both.
- **Rationale**: the roadmap's merge order says 007 must merge before 008, because both edit
  `central.py`. 003 sets where ports live (roadmap decision 003-B). On 2026-11-17, 003 is
  uncommitted work in its worktree and 007 has only its spec. Planning on today's `main` would make
  008 redo, and then conflict with, both.
- **Alternatives**: plan on the current `main` and absorb 003 and 007 later (rejected: double
  conflict in `central.py`, and ports would move twice); fold 003 and 007 into 008 (rejected:
  breaks the roadmap's one-package-per-spec rule).

## R2. Inner home for `RunState`: new package `rescue/state/`

- **Decision**: move `RunState` to `rescue/state/run_state.py`, re-exported from
  `rescue/state/__init__.py`. Allowed imports: `rescue.mission.models`, `rescue.market.models`,
  `rescue.values` and the standard library.
- **Rationale**: adapters need `RunState`, and 003's temporary `adapters → application.state`
  exception must go (FR-007). `RunState` composes the mission, market and communication session aggregates, so it cannot
  live in `values.py`: that module must stay free of domain imports so that every domain package
  can import it. A small package of its own keeps one class per file and gives the contract a
  clear source module.
- **Alternatives**: `rescue/values.py` (rejected: it would import domain models and create
  cycles); `rescue/adapters/ports/` (rejected: `RunState` is data, not a port, and the application
  would then depend on adapters for its central type); leaving it in `application` with the
  exception kept (rejected by FR-007).

## R3. Use case shape: module-level functions with injected ports

- **Decision**: each use case is one function,
  `def <use_case>(command, *, store, id_source=None, simulator=None) -> Result[...]`. It takes only
  the ports it uses, keyword-only. Mutating services build an inner `operation(state)` and call
  `store.transact(operation)` once. Queries call `store.snapshot()`, or use `transact` with an
  identity operation, exactly as the code does today.
- **Rationale**: cosmic-python says "one function or class per use case" and `BP-INJECT-ADAPTERS`.
  Clean architecture says focused use cases with role-sized dependencies. Functions need no
  construction, no shared mutable state and no class hierarchy, and a test can call one with fakes
  directly. `RescueCentral` keeps its frozen fields and passes them on. Each move is a cut-and-paste
  of the method body with `self.<port>` replaced by a parameter.
- **Alternatives**: one class per use case with `__call__` (rejected: adds construction and
  boilerplate, with no state to hold); a unit-of-work and message bus (rejected: constitution IV
  requires a documented need, and `TransactionStore` already gives atomic publish); passing
  `RescueCentral` into services, as `_create_request` does today (rejected: it hides the
  dependencies and is the coupling FR-005 removes).

## R4. Breaking the import cycle: `Simulator` port plus a lazy outer adapter

- **Decision**: add `Simulator(ABC)` with
  `simulate(scenario: RescueScenario, policy: MobilisationPolicy, simulation_id: Id) -> RunSnapshot`
  in `rescue/adapters/ports/simulator.py`. `compare_policies` receives it by injection.
  `RunnerSimulator(Simulator)` in `rescue/experiments/simulator.py` delegates to
  `experiments.runner.simulate` through a function-local import. `bootstrap.new_run` builds it and
  passes it to `RescueCentral(simulator=...)`.
- **Rationale**: today `application.central → experiments.runner → bootstrap → application.central`
  is a cycle. With the port, `application` has no edge to `runner`, so no cycle passes through
  `application` (SC-003). `runner` imports `bootstrap` at module level, so the adapter must load
  `runner` lazily. Otherwise `bootstrap → experiments.simulator → runner → bootstrap` would fail at
  import time. That last edge belongs to 009 ("inject run factory"), which removes the lazy import.
  The compromise sits in the outermost package that can hold it, and it is documented (clean
  architecture: "keep it at the outermost layer, document the violation").
- **Alternatives**: keep the lazy import inside `application` (rejected by FR-006); define the
  port in `application` (rejected: the project's decision is that ports live in `adapters/ports/`);
  put the adapter in `bootstrap.py` (rejected: 003 says `bootstrap` defines no adapters); inject the
  run factory into `runner` now (rejected: that is 009's scope).
- **Consequence for 003's adapters allowlist**: `adapters/ports/simulator.py` imports the domain
  types `rescue.experiments.models` and `rescue.mobilisation.models`. The allowlist becomes
  `rescue.state`, `rescue.values`, the domain model modules and the standard library, and drops
  `rescue.application.state`. Ports speak in domain types; this is the cosmic-python rule
  "adapters import models".

## R5. Import contracts and allowlist

- **Decision**:
  1. New import-linter contract `application-inward` (forbidden): source `rescue.application`;
     forbidden `rescue.adapters.memory`, `rescue.bootstrap`, `rescue.demo`,
     `rescue.experiments.runner`, `rescue.experiments.simulator`, `rescue.experiments.timeline`.
     It replaces `application-no-memory` and drops `allow_indirect_imports`, so indirect paths
     through another module are caught too.
  2. New contract `state-inward` (forbidden): source `rescue.state`; forbidden
     `rescue.application`, `rescue.adapters`, `rescue.bootstrap`, `rescue.demo`,
     `rescue.experiments`, `rescue.mobilisation`. `rescue.communication` is allowed (`session_index` holds
     `CommunicationSession` values; the state contract forbids only the outer packages).
  3. Add `rescue.state` to the source modules of `domain-io`.
  4. AST allowlist test `test_application_imports_only_allowed_modules` covers every `import`
     node, including function-local ones. Allowed: the standard library, `rescue.values`,
     `rescue.state`, `rescue.adapters.ports`, the domain packages (`mission`, `market`,
     `mobilisation`, `communication`), `rescue.experiments.models`, `rescue.experiments.results`
     and `rescue.application` itself.
  5. `test_no_cycles.py` uses grimp: build the `rescue` graph and assert that no module upstream
     of `rescue.application` is also downstream of it.
  6. Update the reviewed contract table in `test_declared_import_contracts_match_the_reviewed_table`.
- **Rationale**: FR-006 asks for an allowlist. import-linter has only forbidden, layers and
  independence contracts, so the AST test supplies the allowlist, the same pattern as 003. In FR-006,
  "experiments" means the non-domain experiment modules. `experiments.models` and
  `experiments.results` are already declared domain in `domain-outward`, and `compare_policies`
  needs their types. grimp 3.20 is already locked as an import-linter dependency.
- **Alternatives**: a layers contract over the whole package (rejected: that is 010's "full layer
  contract"); forbidding all of `rescue.experiments` (rejected: the scenario and snapshot types are
  domain data the comparison returns).

## R6. One deep-immutability implementation in `rescue/values.py`

- **Decision**: add `is_deeply_immutable(value: object) -> bool` to `rescue/values.py`, with the
  body of `application/state._deeply_immutable`. Delete both that function and
  `experiments/models._frozen_tree`. Both callers import the new function.
- **Rationale**: the two functions are identical line for line (checked 2026-11-17). `values.py`
  is the standard-library-only module that both callers may import (FR-007). It moves the
  function-local `dataclasses` import out of `experiments/models.py`.
- **Alternatives**: put it in `rescue/state/` (rejected: `experiments.models` would then import
  state and grow a new edge); keep both copies (rejected by FR-007).

## R7. One file per type: `contracts/` package with re-exports

- **Decision**: `rescue/application/contracts.py` becomes the package `rescue/application/contracts/`:
  `result.py` (`Result`), `result_status.py`, `error_reason.py`, `snapshots.py` (the eight
  `*Snapshot` aliases, moved from `central.py`), and `commands/<command>.py` for each of the 14
  commands. `contracts/__init__.py` re-exports every name listed in `__all__`.
- **Rationale**: FR-002 asks for one file per type, and it lets package exports keep existing
  imports working. `from rescue.application.contracts import X` and
  `from rescue.application import contracts` both still work, so the importers (demo, runner and
  six test modules) need no edit. Aliases are not definitions, so all eight share one file.
- **Alternatives**: rename to `commands/` and `results/` at the top of `application` (rejected:
  every importer changes, for no gain).

## R8. Shared orchestration: one file per helper in `application/shared/`

- **Decision**: each private helper in `central.py` moves verbatim to its own file in `shared/`,
  under the public name in [data-model.md](data-model.md) §4. `_create_request` becomes
  `open_request(state, ..., id_source)`, without the `central` parameter. `_close_request` and the
  duplicated body of `expire_request` become one `close_pending_request(state, mission_id,
  request_id, outcome, at, reason, id_source, guard=None)`. `expire_request` passes its deadline
  check as `guard`. The guard runs after the pending check and before `apply_outcome`, the same
  order as today.
- **Rationale**: FR-005 requires one implementation of shared orchestration. Before the facade is
  cut over, the integration suites (`timing`, `resilience`) pin the behaviour of the only real
  merge, which is cancel/expire.
- **Alternatives**: leave `expire_request` duplicated (rejected by FR-005); push the lookup helpers
  into domain rules (rejected: out of scope, and the lookups work over `RunState`, which is not a
  domain aggregate).

## R9. Docstrings, layout and diagram checks: reuse 004's tests, parametrised

- **Decision**: rename `tests/architecture/mission_layout/` to `tests/architecture/package_layout/`
  and parametrise its three tests over the packages `("mission", "application")`. Mission keeps
  its label rule (two labels on private definitions). Application requires all four labels on
  every module, class and function, private ones included (FR-003). Add
  `test_application_shape.py`, which checks two things. First, every `RescueCentral` public method
  body is a single `return <service>(...)`. Second, every file under `application/services/` is at
  most 250 lines.
- **Rationale**: one implementation of each check (the same rule the spec applies to code). 004's
  tests already parse docstrings, check that `Diagram:` paths exist and compare diagram fields
  with dataclass fields.
- **Alternatives**: copy the tests into an `application_layout/` folder (rejected: two copies
  would drift).

## R10. Diagrams: Application namespace, plus a design view per feature

- **Decision**: add `docs/architecture/diagrams/rescue-domain-model/namespaces/Application/` with
  `class-diagram.mmd` and `entity-relationship-diagram.mmd`, rendered to `.svg` with the same tool
  as the existing namespaces. Link both from the diagram `README.md`. The UML view shows the
  facade, the 19 services (grouped by folder), the shared helpers, the four ports, `Result` and the
  commands, with dependencies only. The ER view shows `RunState` and what it owns: `B3Market` 1–1,
  `Mission` 1–N, the command, message, delivery and decision indexes, policies, scenarios and
  completed runs. Services are not ER entities. Feature-level design diagrams go in
  [design-diagrams.md](design-diagrams.md).
- **Rationale**: FR-004 and the spec's edge case "services are not invented as ER entities". The
  existing namespaces use this exact layout, so the 004 diagram test can include the new files.
- **Alternatives**: extend `domain-model.mmd` (rejected: it is the domain view, and orchestration
  would blur it).

## Best-practice references checked (2026-11-17)

- Cosmic Python ch. 4 (service layer) and ch. 13 (dependency injection): functions taking
  abstract dependencies, wired in a bootstrap composition root. This matches R3 and R4.
- import-linter 2.16 contract types: `forbidden`, `layers`, `independence`, `protected`,
  `acyclic_siblings`. There is no allowlist type, hence the AST test in R5. `acyclic_siblings`
  checks siblings only and cannot express "no cycle through application", hence grimp.
- PEP 810 (explicit lazy imports) targets Python 3.15, so it is not available on 3.14.10. R4
  uses a function-local import.
