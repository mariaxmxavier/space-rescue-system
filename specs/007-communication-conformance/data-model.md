# Data Model: Communication

All classes are `@dataclass(frozen=True, slots=True)` values, and all vocabularies are `StrEnum`. `Id`, `Instant` and the `normalize_*` helpers come from `rescue.values`. Fields of the two existing classes are unchanged unless marked **new**.

## Vocabularies (`models/vocabulary/`, one file per enum)

| Enum | Values |
|------|--------|
| `DeliveryDisposition` | `applied`, `ignored`, `lost`, `rejected`, `late` |
| `DeliveryReason` | `response_applied`, `identity_conflict`, `transport_loss`, `unknown_request`, `invalid_input`, `closed_request`, `deadline_expired`, `unknown_mission`, `unknown_ship`, `insufficient_demand`, `insufficient_capacity`, `unavailable`, `expired_quote`, `revision_conflict`, `duplicate_sequence` |
| `FlowDirection` | `inbound` (ship → central), `outbound` (central → ship) |
| `RecoveryRejection` | `stale_session`, `recovery_out_of_range`, `recovery_limit`, `recovery_in_progress`, `sequence_rewind` |

## Messages and deliveries

### CommunicationMessage (`models/messages/`, moved unchanged)

| Field | Type | Rule |
|-------|------|------|
| `message_id` | `Id` | non-blank; stable across retries (B3 `orderID` analogue) |
| `correlation_id`, `request_id` | `Id` | non-blank |
| `kind` | `str` | non-blank |
| `payload` | `Payload` | tuple of primitive key/value pairs |
| `sent_at` | `Instant` | normalised |

The message has no session sequence: a retry reuses the message under a fresh envelope.

### MessageDelivery (`models/deliveries/`)

| Field | Type | Rule |
|-------|------|------|
| `delivery_id` | `Id` | non-blank; one per attempt (B3 `secondaryOrderID` analogue) |
| `attempt_number` | `int` | > 0 |
| `received_at` | `Instant \| None` | `None` exactly when disposition is `lost` |
| `disposition` | `DeliveryDisposition` | closed set, previously `str` |
| `reason` | `DeliveryReason` | closed set, previously `str` |
| `communication_rtt_seconds` | `Instant \| None` | `None` when lost |
| `envelope` **new** | `SessionEnvelope \| None` | kw-only, default `None`; `None` when lost |

### DeliveryFacts **new** (`models/deliveries/`)

The primitives the application gathers before classifying. It holds no mission or store types.

| Field | Type | Meaning |
|-------|------|---------|
| `delivery_known` | `bool` | delivery identity already recorded |
| `delivery_identical` | `bool` | the recorded delivery has the same message, attempt, receipt and RTT |
| `message_conflicts` | `bool` | message identity recorded with different content |
| `request_known` | `bool` | the request exists in some mission |
| `request_open` | `bool` | the request is pending |
| `request_expired` | `bool` | the request outcome is expired |
| `submitted_at`, `deadline` | `Instant \| None` | request facts; `None` when unknown or no deadline |
| `sent_at`, `received_at` | `Instant`, `Instant \| None` | from the command |

### DeliveryDecision **new** (`models/deliveries/`)

| Field | Type | Meaning |
|-------|------|---------|
| `disposition` | `DeliveryDisposition \| None` | `None` when nothing is recorded (P6 rows 1-2) |
| `reason` | `DeliveryReason \| None` | as above |
| `action` | `str` literal in `{"none", "record", "expire_then_record", "apply"}` | what the application does to the mission |
| `result_status` | `str` | `applied`, `ignored` or `rejected`, mapped to `Result` |
| `result_reason` | `str \| None` | the `Result` reason; set even when nothing is recorded (row 2: `identity_conflict`) |

`apply` means: call `apply_outcome`. If the mission rule raises, the application records `rejected <reason>` (P6 row 10).

## Sessions (`models/sessions/`)

### SessionEnvelope **new**

| Field | Type | Rule |
|-------|------|------|
| `session_id` | `Id` | non-blank; default `local:<ship_id>` |
| `version` | `int` | > 0 |
| `direction` | `FlowDirection` | |
| `sequence` | `int` | > 0 |

Identity of a sequence: `(run, session_id, version, direction, sequence)`. Comparable only within one session version and direction.

### CommunicationSession **new**

| Field | Type | Rule |
|-------|------|------|
| `session_id` | `Id` | unique within `RunState.session_index` |
| `version` | `int` | > 0; active version |
| `next_inbound` | `int` | ≥ 1; next inbound number central expects |
| `next_outbound` | `int` | ≥ 1; next report number central assigns |
| `reports` | `tuple[DecisionReport, ...]` | retained for the active version; outbound sequences 1..next_outbound-1 in order |
| `gaps` | `tuple[NotApplied, ...]` | every inbound gap notice, in order |
| `outstanding_recovery` | `RecoveryRequest \| None` | at most one |

State transitions:

| Event | Effect |
|-------|--------|
| First envelope for a session | session created at that version, counters 1 |
| Envelope with a higher version | counters reset to 1, reports and gaps cleared, outstanding cleared |
| Envelope with a lower version | rejected `stale_session`, session unchanged |
| Inbound `n == next_inbound` | `next_inbound = n + 1` |
| Inbound `n > next_inbound` | `NotApplied(next_inbound, n - next_inbound)` appended; `next_inbound = n + 1` |
| Inbound `n < next_inbound` | unchanged (duplicate) |
| Report issued | report appended with `next_outbound`; `next_outbound += 1` |
| Synchronise advance | `NotApplied` for the skipped range; `next_inbound = next` |
| Synchronise rewind | rejected `sequence_rewind` |

### NotApplied **new**

`session_id`, `version`, `from_sequence` (> 0) and `count` (> 0). A control: it consumes no business number.

## Recovery (`models/recovery/`)

### DecisionReport **new** (rescue execution report)

| Field | Type | Rule |
|-------|------|------|
| `report_id` | `Id` | from `IdSource` |
| `envelope` | `SessionEnvelope` | outbound direction; sequence = the session's `next_outbound` at issue |
| `message_id`, `delivery_id` | `Id` | the response it reports |
| `mission_id` | `Id \| None` | `None` for unknown request |
| `disposition`, `reason` | vocabularies | same as the delivery |
| `mission_sequence` | `int \| None` | the new history entry's `mission_sequence` when the decision appended history, else `None` |
| `after_mission_sequence` | `int` | ≥ 0; last `mission_sequence` of the mission before this decision (0 if none or unknown) |

Invariant: if `mission_sequence` is set, `mission_sequence == after_mission_sequence + 1`. Replays return the same value, so its identity, numbers and content are unchanged.

### RecoveryRequest **new**

`session_id`, `version`, `from_sequence` (> 0) and `count` (1..1000; the bound is checked by the rule, so a request above it can still be represented and rejected).

### SequenceControl **new**

`session_id`, `version`, `direction` and `next_sequence` (> 0). Used as the end-of-recovery marker (outbound) and as the inbound synchronise command.

### ReportCursor **new** (ship-side view)

`session_id`, `version`, `next_expected` (≥ 1) and `buffered: tuple[DecisionReport, ...]` (sorted by sequence, no duplicates).

## Mission order (reused, not new)

`RequestHistoryEntry.mission_sequence` in `rescue/mission/models/mission/request_history_entry.py`. It is assigned as `len(history) + 1` on commit (research P1). Communication reads it only as an `int` the application passes in.

## Run state and baselines

| Holder | Field **new** | Default |
|--------|---------------|---------|
| `RunState` (`rescue/application/state.py`) | `session_index: tuple[CommunicationSession, ...]` | `()` |
| `RunBaseline`, `RunSnapshot` (`rescue/experiments/models.py`) | `session_index: tuple[object, ...]` | `()` |

Each new index must contain only deeply immutable values, checked by the existing `_deeply_immutable` and `_frozen_tree` helpers.

## Diagram deltas

| Diagram | Change |
|---------|--------|
| Communication class | add `request_id` to message; add `communication_rtt_seconds` and `envelope` to delivery; add the 4 enums, envelope, session, gap notice, report, recovery request, sequence control and report cursor; rules as a note or `<<function>>` classes |
| Communication ER | fix the title (it now says "Mission operations + ShipMarket"); add `COMMUNICATION_SESSION`, `DECISION_REPORT` and `NOT_APPLIED`; delivery gains `session_id`, `version` and `sequence`; report → `REQUEST_HISTORY_ENTRY.mission_sequence` cross-reference |
| scenario-model class / ER | the same communication classes and entities, plus `RunBaseline.session_index` |

Only persisted concepts go in the ER; rules and the ship-side cursor go only in the UML (contracts/maintainability.md).
