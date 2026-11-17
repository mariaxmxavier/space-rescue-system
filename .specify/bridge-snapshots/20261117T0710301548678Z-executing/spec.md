# Feature Specification: Experiments Conformance

**Feature Branch**: `009-experiments-conformance`
**Created**: 2026-11-16 · **Updated**: 2026-11-17 · **Status**: Draft
**Input**: "Simplify the 009 spec. Split `rescue/experiments/` into one class or step per file in
nested folders, give every part a docstring (what, when, why, diagram), keep code and the UML/ER
diagrams in step, and inject the run factory instead of importing bootstrap."

## What experiments does

An experiment replays one seeded rescue scenario under one mobilisation policy, in a fresh run,
and summarises the result so policies can be compared. The same seed always gives the same result.

| Part | Does |
|------|------|
| `RescueScenario` | the seeded set-up: baseline, scripted ship responses, availability changes, communication profiles, horizon, event budget |
| `Timeline` | orders simulated events by instant, then by sequence; stops at the horizon or the event budget |
| `simulate` | starts a fresh run, installs the baseline, schedules events and plays them through the application |
| `summarize` | turns a finished run into a `SimulationResult` |

## The problem today

- `runner.py` imports `rescue.bootstrap.new_run`. That closes the cycle
  `application.central` → `experiments.runner` → `bootstrap` → `application.central`.
- `simulate` is one 260-line function with five closures sharing mutable local state.
- `models.py` holds seven classes; `timeline.py` holds two.

## Target layout

```
rescue/experiments/
  models/
    _validation.py               shared private checks (frozen tree, finite tuple)
    scenario/                    the set-up: RescueScenario owns these
      rescue_scenario.py
      run_baseline.py
      scripted_response.py
      communication_profile.py
    run/                         what a simulation produces
      simulation_run.py
      simulation_result.py
      run_snapshot.py
  timeline/
    timeline_event.py
    timeline.py
  results/
    summarize.py
  simulation/                    the runner: one named step per file
    simulate.py                  entry point; composes the steps
    ports/                       StartRun, RunHandle, SimulationCentral (one per file)
    session.py                   the state the steps share, passed explicitly
    install_baseline.py  schedule_initial_events.py  schedule_request_events.py
    schedule_response.py  scripted_outcome.py  mobilise_mission.py  play_event.py
    events/                      one handler per event kind
    finish_run.py
    _payload.py                  shared private response payload
```

The full file list is in [plan.md](plan.md#source-code-repository-root).

Each package `__init__.py` re-exports its public names, so `rescue.experiments.models`,
`rescue.experiments.results` and the import contracts in `pyproject.toml` keep working.
`rescue.experiments.runner` is removed; its callers import `rescue.experiments.simulation`.

## How the run factory is injected

`simulate(scenario, policy, run_id, *, start_run)` takes the function that opens a fresh run.
Callers pass it:

- `bootstrap.new_run` gives `RescueCentral` its own `new_run` as `start_run`; `central.py` passes
  it on to `simulate` and drops the function-local import of the runner.
- `demo.py` and the tests pass `rescue.bootstrap.new_run`.

Experiments then never imports `rescue.bootstrap`, and the cycle is gone without waiting for 008.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The simulation gets its run by injection (Priority: P1)

**Why**: removes the outward import and breaks the import cycle.

**Independent Test**: a test calls `simulate` with a run factory it passes itself; the
architecture check fails if `rescue/experiments/` imports `rescue.bootstrap`.

**Acceptance Scenarios**:

1. **Given** the import contracts, **When** any experiments module imports `rescue.bootstrap`,
   **Then** `make check-architecture` fails.
2. **Given** a seeded scenario, **When** it is simulated twice with the injected factory, **Then**
   both snapshots are equal to each other and to the result on `main`.
3. **Given** `RescueCentral.compare_policies`, **When** it runs, **Then** it uses the factory it was
   built with and returns the same snapshots as on `main`.

### User Story 2 - Find and understand any experiments part fast (Priority: P1)

A reader opens `rescue/experiments/`, finds each class or step in its own file under a folder that
matches its role, and reads a docstring that says what it does, when it is called, why it exists,
and which diagram shows it.

**Independent Test**: every module, class and public function has the four-part docstring; each
file holds one class or one step.

**Acceptance Scenarios**:

1. **Given** the package, **When** a reader opens `models/scenario/scripted_response.py`, **Then**
   it holds only `ScriptedResponse` and its docstring links the Experiments class diagram.
2. **Given** any existing import of `rescue.experiments.models` or `rescue.experiments.results`,
   **When** the suite runs, **Then** it still resolves.

### User Story 3 - The simulation loop reads in steps (Priority: P2)

`simulate` composes named steps that take and return their state explicitly, with no closures
over shared mutable variables.

**Independent Test**: each step has its own test with a small hand-built input and no full run.

**Acceptance Scenarios**:

1. **Given** the refactor, **When** the comparison, communication and resilience tests run,
   **Then** every result is identical to `main`.

### User Story 4 - Code and diagrams say the same thing (Priority: P2)

**Independent Test**: compare each experiments class's fields with its diagram box; there are no
differences.

**Acceptance Scenarios**:

1. **Given** the diagrams, **When** read, **Then** they show `RunBaseline`, `ScriptedResponse` and
   `RunSnapshot`, `RescueScenario` with `event_budget` and `communication_profiles`, and
   `SimulationRun` with its scenario and policy references, as the code has them.
2. **Given** changed `.mmd` files, **When** rendered, **Then** the `.svg` files match.

### Edge Cases

- The event budget runs out: scheduling one more event raises `DomainValidationError`, as today.
- No event is left before the horizon: the run ends with status `horizon_reached`, as today.
- Two events at the same instant: the sequence number breaks the tie, as today.
- The same seed gives byte-identical snapshots across runs and machines.
- A factory that is not callable, or a scenario with no missions, is rejected with
  `DomainValidationError`, as invalid input is today.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `rescue/experiments/` MUST NOT import `rescue.bootstrap`; `simulate` MUST take the
  run factory as a required keyword argument `start_run`. This is a declared import contract.
- **FR-002**: `RescueCentral` MUST receive `start_run` when built and pass it to `simulate`;
  `bootstrap.new_run` supplies it. `central.py` MUST have no function-local import of experiments.
  These are the only edits allowed in `rescue/application/` and `rescue/bootstrap.py`.
- **FR-003**: Each public class and each simulation step MUST live in its own file, in the layout
  above. Private helpers shared inside a folder live in one private module per folder.
- **FR-004**: Every module, class and public function in `rescue/experiments/` MUST have a
  docstring with **What**, **When called**, **Why** and **Diagram** (repo-relative path to the
  `.mmd`). Private helpers need What and Why only.
- **FR-005**: `rescue.experiments.models` and `rescue.experiments.results` MUST keep exporting every
  name they export today. `rescue.experiments.simulation` MUST export `simulate`.
- **FR-006**: `models/`, `timeline/` and `results/` MUST NOT import `simulation/`, the
  application or the adapters, enforced by a declared contract.
- **FR-007**: The four diagrams that show experiments classes MUST match the code: `namespaces/Experiments/`
  (class and ER), `class-diagrams/scenario-model.mmd` and
  `entity-relationship-diagrams/scenario-model-er.mmd`. Their `.svg` files MUST be regenerated.
  Non-experiments parts stay as they are.
- **FR-008**: Unit tests MUST mirror the code: one test file per class or step under
  `tests/unit/experiments/<folder>/test_<name>.py`. Tests outside `tests/unit/experiments/` only
  change to pass `start_run`.
- **FR-009**: `models/`, `timeline/` and `results/` MUST reach 100% line and branch coverage;
  `simulation/` at least 95%.
- **FR-010**: Behaviour MUST NOT change: the full suite passes, seeded snapshots are equal to
  `main`, and the demo output is byte-identical.

### Key Entities

- **RescueScenario** (aggregate): seed, horizon, event budget, baseline, scripted responses,
  availability changes, communication profiles.
- **RunBaseline**: the missions, market and indexes a run starts from.
- **ScriptedResponse**: how a ship answers its Nth request.
- **CommunicationProfile**: delays, loss, duplication and reordering for one ship.
- **SimulationRun** / **SimulationResult** / **RunSnapshot**: what a finished simulation records.
- **Timeline** / **TimelineEvent**: the ordered events of one run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 0 references to `rescue.bootstrap` in `rescue/experiments/`; 0 import cycles reported.
- **SC-002**: 1 class or step per file; no function in `simulation/` exceeds 60 lines.
- **SC-003**: 100% of experiments modules, classes and public functions carry a four-part docstring.
- **SC-004**: 0 field differences between experiments code and the 4 diagrams that show it.
- **SC-005**: Full suite passes; seeded snapshots and demo output byte-identical to `main`.

## Assumptions

- Depends on 002. 008 is no longer a prerequisite: injecting `start_run` breaks the cycle on its
  own. When 008 splits `central.py` into one service per use case, the compare service takes over
  `start_run`.
- The diagrams follow the code, not the reverse, because behaviour must not change.
- Docstrings follow rule P-0001 and the one-class-per-file layout follows rule P-0002
  (`docs/rules/`).
- No new experiment types, metrics or named status vocabularies are added.
