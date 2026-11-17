# Data Model: Mission

Fields are unchanged from `rescue/mission/models.py` at `main` @ `250084d`, except that outcome,
status and action fields are now typed by their closed vocabulary (`StrEnum`, values unchanged).

## Vocabularies (`models/vocabulary/`, one file per enum)

| Enum | Values |
|------|--------|
| `RequestOutcome` | `pending`, `accepted`, `partially_accepted`, `refused`, `cancelled`, `expired` |
| `ProgressStatus` | `complete`, `awaiting_responses`, `needs_more_help` |
| `HistoryAction` | `request_created`, `accepted`, `partially_accepted`, `refused`, `cancelled`, `expired` |

`RequestOutcome.final()` returns the 5 non-`pending` members. It replaces `_TERMINAL_OUTCOMES`.

## Aggregate: `models/mission/`

### Mission (root)

| Field | Type | Rule |
|-------|------|------|
| `mission_id` | `Id` | non-blank |
| `station_name` | `str` | non-blank |
| `people_count` | `int` | > 0, fixed (`D`) |
| `created_at` | `Instant` | normalised |
| `requests` | `tuple[SeatRequest, ...]` | owned; ids unique |
| `history` | `tuple[RequestHistoryEntry, ...]` | owned; `event_id` unique; `mission_sequence` 1..n |

Invariant (checked by `rules/_accounting.account`): `C >= 0`, `P >= 0`, `C + P <= D`, where
`C` = sum of `confirmed_seats`, `P` = sum of `requested_seats` of `pending` requests.

### MissionData

Registration input: `mission_id`, `station_name`, `people_count`, `created_at` (same rules as Mission).

### SeatRequest

| Field | Type | Rule |
|-------|------|------|
| `request_id`, `command_id`, `mission_id`, `ship_id` | `Id` | non-blank |
| `requested_seats` | `int` | > 0 |
| `confirmed_seats` | `int` | >= 0, see state table |
| `outcome` | `RequestOutcome` | closed set |
| `submitted_at` | `Instant` | |
| `response_received_at` | `Instant \| None` | >= submitted, < deadline; `None` for cancelled/expired |
| `response_deadline` | `Instant \| None` | > submitted |
| `closed_at` | `Instant \| None` | >= submitted |
| `quote_id`, `revision_id`, `decision_id` | `Id \| None` | |

State table (outcome → confirmed):

| From | To | Confirmed | Releases |
|------|----|-----------|----------|
| — | `pending` (via `add_request`) | 0 | adds `requested` to `P` |
| `pending` | `accepted` | = requested | none; its `P` share moves to `C` |
| `pending` | `partially_accepted` | 0 < c < requested | remainder |
| `pending` | `refused` | 0 | all |
| `pending` | `cancelled` | 0 | all; no receipt time |
| `pending` | `expired` | 0 | all; no receipt time |
| any closed | anything | — | rejected, mission unchanged |

### RequestHistoryEntry

`event_id: Id`, `mission_sequence: int (>0)`, `recorded_at: Instant`, `action: HistoryAction`,
`confirmed_seats_delta: int`, `pending_seats_delta: int`, `reason: str`, `message_id: Id | None`.

## Projections: `models/projections/`

### MissionProgress

`demand`, `confirmed`, `pending`, `unconfirmed (= D − C)`, `additional_needed (= D − C − P)`,
`status: ProgressStatus` (`complete` iff `C = D`; `awaiting_responses` iff `C + P = D`; else
`needs_more_help`).

### RequestTiming

`submitted_at`, `response_received_at | None`, `waiting_seconds: decimal` (`Instant` = `Decimal`), `response_elapsed_seconds: decimal | None`.

## Diagram deltas (FR-004)

Apply to the mission parts of all 8 diagrams (see spec FR-004 for the file list):

| Change | Why |
|--------|-----|
| `SeatRequest`: add `mission_id`, `ship_id`, `quote_id`, `revision_id`, `decision_id`; `outcome` type → `RequestOutcome` | fields exist in code |
| `RequestHistoryEntry`: add `message_id`; `action` type → `HistoryAction` | field exists in code |
| `MissionProgress.status` type → `ProgressStatus` | closed vocabulary |
| Ownership: `Mission "1" *-- "0..*" RequestHistoryEntry : records changes` replaces `SeatRequest "1" *-- "1..*" RequestHistoryEntry` | code stores history on `Mission`; entries carry no `request_id` |
| Add `MissionData ..> Mission : registers` | registration input exists in code |
| Add `RequestTiming`; `SeatRequest "1" --> "1" RequestTiming : derives` | projection exists in code |
| Add `<<enumeration>>` boxes `RequestOutcome`, `ProgressStatus`, `HistoryAction` (class diagrams only; ER shows them as typed attributes) | closed vocabularies |

`MissionData` and `RequestTiming` are value objects, not stored; the ER diagrams mark them with a
comment rather than a primary key.
