# Contract: Public import paths

These paths and names are used by `application`, `experiments`, `market`, `mobilisation`, `demo`
and tests. They MUST keep resolving after the split (FR-003).

| Import path | Names it MUST export |
|-------------|----------------------|
| `rescue.mission.models` | `Mission`, `MissionData`, `SeatRequest`, `RequestHistoryEntry`, `MissionProgress`, `RequestTiming`, `RequestOutcome`, `ProgressStatus`, `HistoryAction` |
| `rescue.mission.rules` | `register`, `add_request`, `apply_outcome`, `progress`, `timing` |

Each `__init__.py` lists them in `__all__`. New, deeper paths (for example
`rescue.mission.models.mission.seat_request`) are allowed but not required for callers.

Verification: `tests/architecture/mission_layout/test_one_public_name_per_file.py` also asserts
`set(module.__all__)` equals the table above.
