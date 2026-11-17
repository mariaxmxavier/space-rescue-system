# Feature Specification: Mission Conformance

**Feature Branch**: `004-mission-conformance`
**Created**: 2026-11-16 · **Updated**: 2026-11-16 · **Status**: Draft
**Input**: "Simplify the 004 spec. Split `rescue/mission/` into one class or rule per file in nested
folders, give every part a docstring (what, when, why, diagram), and keep code and the UML/ER
diagrams in step."

## What mission does

A mission is one rescue job: a station needs `D` seats (`people_count`), fixed at registration.
Mission counts seats and nothing else. It never talks to ships, markets or messages; callers give
it facts and it guards the rule.

| Rule | Does |
|------|------|
| `register` | opens a mission with demand `D` |
| `add_request` | asks one ship for `N` seats; they are *pending*; rejected if confirmed + pending + `N` > `D` |
| `apply_outcome` | closes a request (accepted, partially accepted, refused, cancelled, expired); confirmed seats are added, the rest released; closed requests never change |
| `progress` | `complete` (confirmed = `D`), `awaiting_responses` (confirmed + pending = `D`), else `needs_more_help` |
| `timing` | how long a request has waited, or how long the ship took to answer |

Every change appends one history entry to the mission.

## Target layout

```
rescue/mission/
  models/
    vocabulary/                  one file per closed vocabulary
      request_outcome.py  progress_status.py  history_action.py
    _validation.py               shared private checks
    mission/                     the aggregate: Mission owns these
      mission.py
      mission_data.py
      seat_request.py
      request_history_entry.py
    projections/                 derived, read-only views
      mission_progress.py
      request_timing.py
  rules/
    register.py  add_request.py  apply_outcome.py  progress.py  timing.py
    _accounting.py               shared private accounting + history append
```

`models/__init__.py` and `rules/__init__.py` re-export every public name, so existing imports
(`from rescue.mission.models import Mission`, `from rescue.mission.rules import progress`) keep
working unchanged.

## Clarifications

### Session 2026-11-16

- Q: Where do shared private helpers live? → A: One private helper module per folder: `models/_validation.py` and `rules/_accounting.py`.
- Q: Is the history entry `action` a closed vocabulary too? → A: Yes: `HistoryAction` (`request_created` + the 5 final outcomes) in `vocabulary.py`.
- Q: Which diagrams change? → A: The mission parts of all 8 diagrams that show mission classes (MissionOperations, CoreReferences, full domain and scenario, class and ER), `.mmd` and `.svg`.
- Q: How are mission tests laid out? → A: Mirror the code: one test file per class or rule under `tests/unit/mission/models/` and `tests/unit/mission/rules/`, plus `rules/test_invariant_table.py`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find and understand any mission part fast (Priority: P1)

A newcomer or an agent opens `rescue/mission/`, finds each class or rule in its own file under a
folder that matches its diagram role, and reads a docstring that says what it does, when it is
called, why it exists, and which diagram shows it.

**Independent Test**: Every module, class and public function in `rescue/mission/` has a docstring
with the four parts; each file holds one class or one rule.

**Acceptance Scenarios**:

1. **Given** the package, **When** a reader opens `models/mission/seat_request.py`, **Then** it
   holds only `SeatRequest` and its docstring links the MissionOperations class and ER diagrams.
2. **Given** any existing import of `rescue.mission.models` or `rescue.mission.rules`, **When** the
   suite runs, **Then** it still resolves.

### User Story 2 - Code and diagrams say the same thing (Priority: P1)

All 8 diagrams that show mission classes show every mission class and field the code has, and the
code shows nothing those diagrams lack.

**Independent Test**: Compare each class's fields with its diagram box; there are no differences.

**Acceptance Scenarios**:

1. **Given** the diagrams, **When** read, **Then** they include `RequestTiming`, the `SeatRequest`
   ids (`mission_id`, `ship_id`, `quote_id`, `revision_id`, `decision_id`), and show `Mission`
   owning its history (as the code does).
2. **Given** changed `.mmd` files, **When** rendered, **Then** the `.svg` files match.

### User Story 3 - Seat rules are proven for every case (Priority: P2)

One test table applies each of the 5 final outcomes to each reachable request state and checks
`C >= 0`, `P >= 0`, `C + P <= D`, and that closed requests never change.

**Acceptance Scenarios**:

1. **Given** a pending request, **When** any final outcome is applied, **Then** the rules hold and
   the unconfirmed remainder is released.
2. **Given** a closed request, **When** any outcome is applied, **Then** it is rejected and the
   mission is unchanged.
3. **Given** `C < D`, **When** progress is read, **Then** pending seats never make it complete.

### User Story 4 - Outcomes, statuses and history actions are named, not free strings (Priority: P2)

`RequestOutcome`, `ProgressStatus` and `HistoryAction` are the only source of those names. Callers
use them.

**Acceptance Scenarios**:

1. **Given** an unknown outcome or status, **When** a value is built, **Then** it is rejected.
2. **Given** the change, **When** the demo runs, **Then** its output is byte-identical.

### Edge Cases

- Partial acceptance with 0 confirmed is rejected; refusal releases the same seats with a
  different recorded outcome.
- Confirming more than requested is rejected and changes nothing.
- An instant given as a `Decimal`, string or int normalises to the same value.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each public class and each rule MUST live in its own file, in the layout above.
  Private helpers shared inside a folder live in one private module per folder:
  `models/_validation.py` (name, id, instant, quantity checks) and `rules/_accounting.py`
  (seat accounting and history append).
- **FR-002**: Every module, class and public function in `rescue/mission/` MUST have a docstring
  with **What**, **When called**, **Why**, and **Diagram** (repo-relative path to the `.mmd`).
  Private helpers need What and Why only.
- **FR-003**: Public import paths `rescue.mission.models` and `rescue.mission.rules` MUST keep
  exporting every name they export today.
- **FR-004**: Every diagram under `docs/architecture/diagrams/rescue-domain-model/` that shows a
  mission class MUST have its mission parts updated to match the code: `namespaces/MissionOperations/`
  and `namespaces/CoreReferences/` (class and ER), `class-diagrams/domain-model.mmd`,
  `class-diagrams/scenario-model.mmd`, `entity-relationship-diagrams/domain-model-er.mmd` and
  `scenario-model-er.mmd`. Their `.svg` files MUST be regenerated. Non-mission parts stay as they are.
- **FR-005**: Request outcomes, progress statuses and history actions MUST be closed named values
  (`RequestOutcome`, `ProgressStatus`, `HistoryAction`); their string literals outside
  `rescue/mission/` MUST be replaced by them. Stored and rendered text stays the same.
- **FR-006**: Local helpers that duplicate a `rescue.values` helper MUST be removed, or kept with a
  test that shows why.
- **FR-007**: Tests MUST cover every final outcome against every reachable request state, checking
  the seat rules after each, in `tests/unit/mission/rules/test_invariant_table.py`.
- **FR-007a**: Mission unit tests MUST mirror the code: one test file per class
  (`tests/unit/mission/models/test_<class>.py`) and per rule
  (`tests/unit/mission/rules/test_<rule>.py`). `tests/unit/mission/rules/test_mission.py` is split
  into them and removed. Tests outside `tests/unit/mission/` stay where they are.
- **FR-008**: `rescue/mission/` MUST import only `rescue.values` and the standard library, enforced
  by a declared import contract.
- **FR-009**: `rescue/mission/` MUST reach 100% line and branch coverage with no fakes and no I/O.
- **FR-010**: Behaviour MUST NOT change: the full suite passes and the demo output is identical.

### Key Entities

- **Mission** (aggregate): demand `D`, its seat requests and history.
- **MissionData**: registration input.
- **SeatRequest**: one ask to one ship; pending until a final outcome.
- **RequestHistoryEntry**: one recorded change to the mission's seat counts.
- **MissionProgress** / **RequestTiming**: read-only views derived from the mission.
- **RequestOutcome** / **ProgressStatus** / **HistoryAction**: the closed name sets.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 1 class or rule per file; 0 mission files hold two.
- **SC-002**: 100% of mission modules, classes and public functions carry a four-part docstring.
- **SC-003**: 0 field or ownership differences between mission code and the 8 diagrams that show it.
- **SC-004**: 0 outcome, status or history-action string literals outside `rescue/mission/`.
- **SC-005**: 5 outcomes × every reachable state covered; 100% line and branch coverage of the
  package.
- **SC-006**: Full suite passes; demo output byte-identical.

## Assumptions

- Depends on 002. Independent of 003 and 005–007.
- The diagrams follow the code, not the reverse, because behaviour must not change.
- Docstrings are requested by the maintainer and override the global "no comments" default for
  this package.
- Call-site edits outside `rescue/mission/` are limited to swapping string literals for named
  values.
- The one-file-per-class and docstring rule is added to the roadmap for specs 005–010; applying it
  to other packages is out of scope here.
