# Research: Experiments Conformance

## R1. How `simulate` gets a run without importing bootstrap

- **Decision**: `simulate(scenario, policy, run_id, *, start_run: StartRun)`. `StartRun`,
  `RunHandle` and `SimulationCentral` are `typing.Protocol` ports in
  `rescue/experiments/simulation/ports/`. `bootstrap.RunContext` already satisfies `RunHandle`
  structurally, and `bootstrap.new_run` satisfies `StartRun`, so neither changes shape.
- **Rationale**: Clean Architecture's dependency rule. The use case owns the port it needs, and
  the composition root supplies the implementation. `SimulationCentral` lists only the five
  `RescueCentral` methods the runner calls, so experiments never imports `application.central`
  (that import would create a new cycle, `central` → `experiments` → `central`).
- **Alternatives**: annotate with `RunContext` (imports bootstrap again, rejected); a
  `TYPE_CHECKING` import of `RescueCentral` (import-linter counts it, because
  `exclude_type_checking_imports = false`, rejected); untyped `Callable[..., Any]` (loses the
  port's meaning, rejected).

## R2. How `RescueCentral.compare` gets the factory

- **Decision**: add a required field `start_run: StartRun` to the frozen `RescueCentral`
  dataclass. `bootstrap.new_run` passes `start_run=new_run` (a module-level function, so it can
  refer to itself). `central.py` imports `simulate` and `StartRun` at module top, and the
  function-local import at `central.py:1034` goes away.
- **Rationale**: `RescueCentral` is built only in `bootstrap.py:71`, so a required field
  changes exactly one call site. Import order stays acyclic:
  `central` → `experiments.simulation` → `application.contracts` / `adapters.ports`, and
  neither of those imports `central`. `rescue/application/__init__.py` imports nothing.
- **Alternatives**: pass `start_run` on the `ComparePolicies` command (it is a data contract and
  would carry a function, rejected); an optional field defaulting to `None` (moves a wiring error
  to run time, rejected).

## R3. How the closures become explicit steps without changing results

- **Decision**: one `SimulationSession` frozen dataclass carries what the closures shared:
  `handle`, `policy`, `timeline`, `rng`, `sequence` (an `itertools.count(1)`), `response_rules`,
  `profiles` and `ship_ordinals` (a `dict`). Each step is a module-level function that takes the
  session and its own inputs. `nonlocal scenario_sequence` becomes `next(session.sequence)`,
  which yields the same 1, 2, 3, …
- **Rationale**: Timeline, rng, counter and ordinals are already mutable objects, and freezing
  the holder makes every step's dependencies visible in its signature without copying the heap.
  Determinism depends on three call orders that must not move: `rng` draws, `next(sequence)`,
  and `id_source.next_id(...)`. Each step keeps the original statement order.
- **Alternatives**: fully immutable state returned from each step (the timeline heap and the
  application store are mutable by design, so this would need a rewrite and break FR-010,
  rejected); a class with methods (the same closure in another shape, rejected).

## R4. Step split (each function at most 60 lines, SC-002)

| Original | New file | Step |
|----------|----------|------|
| head of `simulate` | `simulation/simulate.py` | validate, start run, compose steps, loop |
| `install_baseline`, `_copy_command_index`, `_baseline_identity_ids` | `simulation/install_baseline.py` | copy the baseline into the fresh store; `baseline_identity_ids` |
| first scheduling block | `simulation/schedule_initial_events.py` | mobilise, availability, expire and response events for the baseline |
| `schedule_request_events` | `simulation/schedule_request_events.py` | events for one new request |
| `_schedule_response` | `simulation/schedule_response.py` | response events per communication profile |
| `_scripted_response` | `simulation/scripted_outcome.py` | pure outcome and seat choice from a rule and rng |
| `mobilise_mission` | `simulation/mobilise_mission.py` | mobilise and create requests |
| `while` body | `simulation/play_event.py` + `simulation/events/` | dispatch by kind: `publish_availability.py`, `expire_request.py`, `record_response.py` |
| tail of `simulate` | `simulation/finish_run.py` | snapshot plus `summarize` |
| `_ResponsePayload` | `simulation/_payload.py` | private payload |

## R5. Import contracts (import-linter 2.16)

- **Decision**:
  - Add `rescue.experiments.timeline` to the sources of `domain-outward` and `domain-io`.
  - Add `experiments-pure-core`: `models`, `timeline` and `results` must not import
    `rescue.experiments.simulation` (FR-006).
  - Add `experiments-no-bootstrap`: `rescue.experiments` must not import `rescue.bootstrap` or
    `rescue.demo` (FR-001).
  - The count asserted in `tests/architecture/boundaries/test_architecture.py` goes from 11 to
    13, and its reviewed table gets the two new rows.
- **Rationale**: `forbidden` contracts need no sibling-layer syntax, so there is no risk from
  version-specific `layers` grammar (that documentation could not be fetched).
- **Alternatives**: one `layers` contract with independent siblings (syntax unverified for 2.16,
  rejected).

## R6. Architecture tests for layout and docstrings

- **Decision**: add `tests/architecture/experiments_layout/` with
  `test_one_public_name_per_file.py`, `test_docstrings.py` and `test_diagrams_match_code.py`,
  copied from `mission_layout/` with the root and expected tables changed. Do not generalise the
  mission tests.
- **Rationale**: the mission tests pin mission-specific tables, and a shared helper would edit
  004's files outside this scope. The duplication is accepted for now; a shared helper is a
  candidate for 010.

## R7. Diagram deltas (code is the source of truth)

| Class | Diagram today | Code |
|-------|---------------|------|
| RescueScenario | 8 fields | + `event_budget`, `communication_profiles`; `baseline` → RunBaseline, `response_rules` → ScriptedResponse |
| CommunicationProfile | no `ship_id` | + `ship_id` |
| SimulationRun | 4 fields | + `scenario_id`, `scenario_revision`, `policy_id`, `policy_revision`, `result` |
| RunBaseline, ScriptedResponse, RunSnapshot | missing | added |
| Timeline, TimelineEvent | missing | not added: run-time scheduling, not domain data |

Files: `namespaces/Experiments/{class-diagram,entity-relationship-diagram}.mmd`,
`class-diagrams/scenario-model.mmd` and `entity-relationship-diagrams/scenario-model-er.mmd`.
Each `.svg` is regenerated with Mermaid CLI 11.17.0, as in 004.

## R8. Local environment risk

`uv sync --locked` fails on this Windows machine. With the free-threaded CPython 3.14.10 picked
first, `ortools==9.15.6755` has no matching wheel. Commit `33652fc` says to set `UV_PYTHON` to a
GIL interpreter. The gates are run that way, or in CI. This is out of scope for 009.
