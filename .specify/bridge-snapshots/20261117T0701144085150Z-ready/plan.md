# Implementation Plan: Experiments Conformance

**Branch**: `009-experiments-conformance` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/009-experiments-conformance/spec.md`

## Summary

Split `rescue/experiments/` into one public class or step per file:
- `models/scenario/` and `models/run/` mirror the Experiments UML;
- `timeline/` and `results/` hold the pure parts;
- `simulation/` replaces `runner.py` with named steps of at most 60 lines.

`simulate` receives its run through a `start_run` port that it owns (Clean Architecture
dependency rule). `RescueCentral` gets that factory from `bootstrap.new_run`, which breaks the
`central` → `experiments` → `bootstrap` → `central` import cycle without waiting for 008.

Every module, class and public function gets the four-part docstring. The 4 Experiments diagrams
follow the code. Two new import contracts and three layout tests enforce all of this. Behaviour
does not change: seeded snapshots and the demo output stay byte-identical.

Execution: superpowers subagent-driven development. `[P]` tasks own disjoint files.

## Technical Context

**Language/Version**: Python 3.14.10 (`.python-version`), uv 0.13.8

**Primary Dependencies**: standard library inside `rescue/experiments/` (`dataclasses`,
`decimal`, `heapq`, `itertools`, `random`, `typing.Protocol`); dev: ruff, pytest, pytest-cov,
coverage, import-linter 2.16 (pinned in `pyproject.toml`); Mermaid CLI 11.17.0 for `.svg`

**Storage**: N/A (in-memory run store supplied by the injected factory)

**Testing**: pytest; unit tests per class and step with hand-built inputs; integration tests
through `new_run`; architecture tests under `tests/architecture/experiments_layout/`

**Target Platform**: CPython 3.14 (GIL build; see research R8 for the Windows install note)

**Project Type**: library package inside a single Python project

**Performance Goals**: N/A (no behaviour change)

**Constraints**:
- seeded snapshots and demo output byte-identical to `main`;
- `rng`, sequence and `id_source` call orders unchanged (research R3);
- edits outside `rescue/experiments/` limited to `central.py`, `bootstrap.py`, `demo.py`,
  `pyproject.toml`, `Makefile` and the tests listed in `contracts/start-run.md`

**Scale/Scope**:
- 4 source files (≈910 lines) become ≈27 files;
- 3 callers of `simulate` in `rescue/` and 3 in tests;
- 4 `.mmd` and 4 `.svg` diagrams;
- 4 test files (14 tests) become one test file per class or step

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How this plan keeps it | Status |
|-----------|------------------------|--------|
| I. Safe Seat Accounting | No rule changes; the simulation still drives every seat change through `RescueCentral` | PASS |
| II. Final Request Outcomes | `scripted_outcome` moves unchanged; the outcome × seats table gets its own unit test | PASS |
| III. Reliable Operations | Loss, duplication and reordering paths move unchanged; the `test_communication` and `test_resilience` integration suites are the guard | PASS |
| IV. Simple Design | The only new abstraction is the `StartRun`/`RunHandle`/`SimulationCentral` port that breaks the cycle (documented need: FR-001/002); `SimulationSession` replaces closures 1:1 | PASS |
| V. Evidence and Explainability | Demo byte-identical and a seeded-snapshot equality test are the exit gate | PASS |
| Workflow: parallel writers own disjoint files | Each `[P]` task below names its files | PASS |
| Exact versions | No new dependency | PASS |

Post-design re-check (after Phase 1): PASS, no violations; Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/009-experiments-conformance/
├── spec.md
├── plan.md               # this file
├── research.md           # Phase 0: R1–R8
├── data-model.md         # Phase 1: entities, fields, ports, session
├── quickstart.md         # Phase 1: how to verify
├── contracts/
│   ├── start-run.md          # simulate signature, ports, callers
│   ├── public-imports.md     # names each import path keeps exporting
│   ├── docstring.md          # four-part docstring + diagram per folder
│   └── import-contracts.md   # import-linter changes (11 → 13)
└── tasks.md              # /speckit-tasks (not created here)
```

### Source Code (repository root)

```text
rescue/experiments/
├── __init__.py
├── models/
│   ├── __init__.py                     re-exports the 7 model classes
│   ├── _validation.py                  frozen_tree, finite_tuple
│   ├── scenario/
│   │   ├── __init__.py
│   │   ├── rescue_scenario.py          RescueScenario (aggregate)
│   │   ├── run_baseline.py             RunBaseline
│   │   ├── scripted_response.py        ScriptedResponse
│   │   └── communication_profile.py    CommunicationProfile
│   └── run/
│       ├── __init__.py
│       ├── simulation_run.py           SimulationRun
│       ├── simulation_result.py        SimulationResult
│       └── run_snapshot.py             RunSnapshot
├── timeline/
│   ├── __init__.py
│   ├── timeline_event.py
│   └── timeline.py
├── results/
│   ├── __init__.py
│   └── summarize.py
└── simulation/
    ├── __init__.py                     simulate + the 3 ports
    ├── ports/
    │   ├── __init__.py
    │   ├── start_run.py                StartRun
    │   ├── run_handle.py               RunHandle
    │   └── simulation_central.py       SimulationCentral
    ├── _payload.py                     _ResponsePayload
    ├── session.py                      SimulationSession
    ├── simulate.py
    ├── install_baseline.py             install_baseline, baseline_identity_ids
    ├── schedule_initial_events.py
    ├── schedule_request_events.py
    ├── schedule_response.py
    ├── scripted_outcome.py
    ├── mobilise_mission.py
    ├── play_event.py
    ├── events/
    │   ├── __init__.py
    │   ├── publish_availability.py
    │   ├── expire_request.py
    │   └── record_response.py
    └── finish_run.py

tests/unit/experiments/
├── models/      test_rescue_scenario.py, test_run_baseline.py, test_scripted_response.py,
│                test_communication_profile.py, test_simulation_run.py,
│                test_simulation_result.py, test_run_snapshot.py
├── timeline/    test_timeline_event.py, test_timeline.py
├── results/     test_summarize.py
└── simulation/  test_simulate.py, test_install_baseline.py, test_schedule_initial_events.py,
                 test_schedule_request_events.py, test_schedule_response.py,
                 test_scripted_outcome.py, test_mobilise_mission.py, test_play_event.py,
                 test_finish_run.py

tests/architecture/experiments_layout/
├── test_one_public_name_per_file.py    one public name per file, export tables, ≤60-line functions
├── test_docstrings.py
└── test_diagrams_match_code.py
```

**Structure Decision**: in cosmic-python terms, `models/`, `timeline/` and `results/` are the
domain-model layer: pure, no I/O, 100% coverage. `simulation/` is the service layer: it
orchestrates use cases through `SimulationCentral` and owns its ports (research R1). The two new
import contracts declare that direction (`contracts/import-contracts.md`). The folder names
mirror the Experiments class diagram.

## Delivery strategy (subagent-driven, parallel)

Each wave ends with `make check-all` green before the next starts.

| Wave | Tasks | Parallel | Owns |
|------|-------|----------|------|
| 0 | Bridge handoff points at 009; capture the `main` demo output and a seeded snapshot fixture | no | bridge state, `tests/unit/experiments/simulation/fixtures/` |
| 1 | Injection first, while still in `runner.py`: add the ports and `start_run`; `RescueCentral.start_run`; `bootstrap` passes `new_run`; `demo` and tests pass it; remove the function-local import; add the 2 contracts and the 11 → 13 test update | no | `runner.py`, `simulation/ports/`, `central.py`, `bootstrap.py`, `demo.py`, `pyproject.toml`, `test_architecture.py`, the 3 test files |
| 2 | Foundation: `git mv` `models.py` → `models/_legacy.py`, `timeline.py` → `timeline/_legacy.py`, `results.py` → `results/_legacy.py`, `runner.py` → `simulation/_legacy.py`, with `__init__` re-exports; `models/_validation.py`; layout tests marked `xfail(strict=True)` | no | listed files |
| 3 | One subagent per model class, timeline class and `summarize`: new file + unit test | **[P] ×10** | one source + one test file each |
| 4 | Simulation steps: `_payload.py` + `session.py` (serial), then one subagent per step: new file + unit test | **[P] ×9** after serial part | one step + one test each |
| 5 | Integration: point the `__init__`s at the new files; delete the `_legacy.py` files and the old 4 test files; remove the `xfail`s; Makefile coverage gates (100 for models, timeline, results; 95 for simulation) | no | `__init__`s, `_legacy.py` files, old tests, `Makefile` |
| 6 | Diagrams: one subagent per `.mmd` + `.svg` pair (research R7) | **[P] ×4** | one pair each |
| 7 | Verify per `quickstart.md`: `make check-all`, demo diff, seeded-snapshot equality, coverage | no | read-only |

Why wave 1 comes first: injection is a behaviour-neutral signature change that removes the cycle
in a small diff, so the file split that follows starts from an acyclic graph. Waves 3 and 4 run in
parallel safely because `_legacy.py` keeps every name re-exported until wave 5 swaps the
`__init__`s in one task.

Each subagent brief carries the FR it serves, its owned files, `contracts/docstring.md`, the
no-behaviour-change rule (call order of `rng`, `next(sequence)` and `next_id`), and the gate
command.

## Complexity Tracking

No violations.
