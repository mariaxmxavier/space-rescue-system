# Implementation Plan: Mission Conformance

**Branch**: `004-mission-conformance` | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-mission-conformance/spec.md`

## Summary

Split `rescue/mission/` into one public class or rule per file, in folders that mirror the
MissionOperations UML (`models/mission/` = what `Mission` owns, `models/projections/` = what it
derives, `rules/` = one transition per file). Add closed vocabularies (`RequestOutcome`,
`ProgressStatus`, `HistoryAction`) as `StrEnum`s so stored and rendered text is unchanged. Give
every module, class and public function a What / When called / Why / Diagram docstring. Update the
mission parts of 8 diagrams to match the code, and enforce all of it with architecture tests and an
import contract. Behaviour does not change.

Execution: superpowers subagent-driven development, one fresh subagent per task, with `[P]` tasks
dispatched together because each owns disjoint files (Constitution, Development Workflow).

## Technical Context

**Language/Version**: Python 3.14.10 (`.python-version`), uv 0.13.8

**Primary Dependencies**: standard library only inside `rescue/mission/` (`dataclasses`, `decimal`,
`enum.StrEnum`); dev: ruff 0.17.5, pytest 9.2.0, pytest-cov 7.1.0, coverage 7.17.3,
import-linter 2.16 (all pinned in `pyproject.toml`). Diagrams: Mermaid CLI 11.17.0 (`mmdc`, installed).

**Storage**: N/A (pure domain package)

**Testing**: pytest; unit tests with no fakes and no I/O; architecture tests under
`tests/architecture/mission_layout/`

**Target Platform**: any platform running CPython 3.14

**Project Type**: library package inside a single Python project

**Performance Goals**: N/A (no behaviour change)

**Constraints**: no behaviour change; demo output byte-identical; existing import paths
`rescue.mission.models` / `rescue.mission.rules` keep every name; mission imports only
`rescue.values` + stdlib

**Scale/Scope**: 2 source files (≈500 lines) → 15 files; ≈60 mission literal comparison sites in 9
caller files; 8 `.mmd` + 8 `.svg` diagrams

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How this plan keeps it | Status |
|-----------|------------------------|--------|
| I. Safe Seat Accounting | Code moves unchanged; invariant table test (FR-007) proves `C>=0`, `P>=0`, `C+P<=D`, complete only at `C=D` | PASS |
| II. Final Request Outcomes | Outcome × state table covers all 5 outcomes, closed requests immutable, confirmation ≤ requested | PASS |
| III. Reliable Operations | Invalid operations keep the mission unchanged: asserted in the table test | PASS |
| IV. Simple Design | No new abstraction except the three enums the spec requires; helpers in one private module per folder | PASS |
| V. Evidence and Explainability | Full suite + byte-identical demo is the exit gate | PASS |
| Workflow: parallel writers own disjoint files | Every `[P]` task below names its files; no two `[P]` tasks touch one file | PASS |
| Exact versions | No new dependency | PASS |

Post-design re-check (after Phase 1): PASS, no violations; Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/004-mission-conformance/
├── spec.md
├── plan.md               # this file
├── research.md           # Phase 0
├── data-model.md         # Phase 1: entities, fields, diagram deltas
├── design-diagrams.md    # Phase 1: layout, dependency and lifecycle diagrams
├── quickstart.md         # Phase 1: how to verify
├── contracts/
│   ├── public-imports.md     # names each import path must keep exporting
│   ├── docstring.md          # the four-part docstring format
│   └── import-contracts.md   # import-linter contracts added
└── tasks.md              # /speckit-tasks (not created here)
```

### Source Code (repository root)

```text
rescue/mission/
├── __init__.py
├── models/
│   ├── __init__.py                  re-exports every public model name
│   ├── vocabulary/              request_outcome.py, progress_status.py, history_action.py (one class each)
│   ├── _validation.py               normalize_name, optional_id, optional_instant, signed_quantity, normalize_instant
│   ├── mission/
│   │   ├── __init__.py
│   │   ├── mission.py               Mission (aggregate root)
│   │   ├── mission_data.py          MissionData
│   │   ├── seat_request.py          SeatRequest
│   │   └── request_history_entry.py RequestHistoryEntry
│   └── projections/
│       ├── __init__.py
│       ├── mission_progress.py      MissionProgress
│       └── request_timing.py        RequestTiming
└── rules/
    ├── __init__.py                  re-exports register, add_request, apply_outcome, progress, timing
    ├── _accounting.py               account, append_history
    ├── register.py
    ├── add_request.py
    ├── apply_outcome.py
    ├── progress.py
    └── timing.py

tests/unit/mission/
├── models/
│   ├── test_request_outcome.py, test_progress_status.py, test_history_action.py
│   ├── test_mission.py
│   ├── test_mission_data.py
│   ├── test_seat_request.py
│   ├── test_request_history_entry.py
│   ├── test_mission_progress.py
│   └── test_request_timing.py
└── rules/
    ├── test_register.py
    ├── test_add_request.py
    ├── test_apply_outcome.py
    ├── test_progress.py
    ├── test_timing.py
    └── test_invariant_table.py

tests/architecture/mission_layout/
├── test_one_public_name_per_file.py
├── test_docstrings.py
└── test_diagrams_match_code.py
```

**Structure Decision**: Layout B from the spec. `rules/` stays a peer of `models/` (not
`services/`): in cosmic-python terms both are the models layer, since every rule is a pure
transformation with no I/O and no orchestration. `models/` must not import `rules/`; this is
declared as an import-linter layers contract.

## Delivery strategy (subagent-driven, parallel)

Each wave ends with `make check-all` green before the next wave starts. Within a wave, `[P]` tasks
run as parallel subagents; each owns only the files it lists.

| Wave | Tasks | Parallel | Owns |
|------|-------|----------|------|
| 0 | Bridge handoff points at 004 (`.specify/superpowers-handoff.json` via the bridge handoff skill) | no | bridge state |
| 1 | Foundation: `git mv` `models.py` → `models/_legacy.py` and `rules.py` → `rules/_legacy.py` with `__init__` re-exports; `vocabulary/` (3 files) + tests; `_validation.py`; architecture tests written and marked `xfail(strict=True)` until wave 4 | no | listed files |
| 2 | One subagent per model class: new file + its unit test (TDD: test imports the new path first) | **[P] ×6** | one model file + one test file each |
| 3 | `_accounting.py` first (serial), then one subagent per rule: new file + its unit test; plus `test_invariant_table.py` | **[P] ×6** after `_accounting.py` | one rule file + one test file each |
| 4 | Integration: point `models/__init__.py` and `rules/__init__.py` at the new files, delete both `_legacy.py`, fold `tests/unit/mission/rules/test_mission.py` into the per-rule tests and delete it, remove the `xfail`s | no | mission `__init__`s, `_legacy.py` files, old test |
| 5 | Caller literal swaps, one subagent per caller file; import contracts + Makefile coverage gate | **[P] ×10** | one caller file each; `pyproject.toml` + `Makefile` for the contract task |
| 6 | Diagrams: one subagent per diagram pair (`.mmd` + its `.svg`); diagram README note | **[P] ×8** | one `.mmd` + `.svg` each |
| 7 | Verify: `make check-all`, demo byte-identical diff, coverage 100% for `rescue/mission` | no | none (read-only) |

Why waves 2 and 3 can run in parallel without editing a shared file: new files are created beside
`_legacy.py`, which the package `__init__`s keep re-exporting, so the suite stays green. Only wave 4
swaps the `__init__`s, and one agent does it (research R8).

Each subagent brief carries: the spec FR it serves, its owned files, the docstring contract, the
"no behaviour change" rule, and the gate command. Two-stage review (spec compliance, then code
quality) runs per task, as the subagent-driven-development skill prescribes.

## Complexity Tracking

No violations.
