# Contract: Application surface for communication

Plain request and response values cross the boundary. Every method runs inside one `TransactionStore.transact` call and returns `Result[T]` (`rescue/application/contracts.py`). A rejection never publishes partial state.

## Commands (`contracts.py`)

| Command | Fields | Change |
|---------|--------|--------|
| `RecordResponse` | existing fields + `envelope: SessionEnvelope \| None = None` | **extended**. `None` uses the default local session (research P3) |
| `RecoverReports` | `session_id`, `version`, `from_sequence`, `count` | **new** |
| `SynchroniseInbound` | `session_id`, `version`, `next_sequence` | **new** |

## Methods on `RescueCentral`

| Method | Returns | Behaviour |
|--------|---------|-----------|
| `record_response(RecordResponse)` | `Result[RequestSnapshot]` | Precedence of research P6. Statuses and reasons for unsequenced calls are unchanged. Also issues a `DecisionReport` (P7). |
| `recover_reports(RecoverReports)` | `Result[tuple[DecisionReport \| SequenceControl, ...]]` | Retained reports in outbound order, then one `SequenceControl(next_outbound)`. Read-only. |
| `synchronise_inbound(SynchroniseInbound)` | `Result[CommunicationSession]` | Advance records `NotApplied`; equal is a no-op; rewind is rejected. |
| `get_session(session_id)` | `Result[CommunicationSession]` | Diagnostics: version, both counters, gaps and reports. `rejected unknown_session` when the session is absent. |
| `get_deliveries(message_id)` | unchanged | Deliveries now include `envelope`. |
| `get_history(mission_id)` | unchanged | `mission_sequence` is the mission order number. |

## Result reasons added to `ErrorReason`

`duplicate_sequence`, `stale_session`, `sequence_rewind`, `recovery_out_of_range`, `recovery_limit`, `recovery_in_progress` and `unknown_session`. `ResultStatus` is unchanged. A `NotApplied` notice is a diagnostic in the session, not a result status: the message that revealed the gap still gets its own business result.

## Outcomes by story

| Spec scenario | Call | Expected |
|---------------|------|----------|
| 2.2 inbound 3 while expecting 2 | `record_response` with envelope seq 3 | business result of message 3; `get_session` shows `NotApplied(2, 1)` and `next_inbound == 4` |
| 2.3 delayed old sequence | `record_response` with seq below expected | `ignored duplicate_sequence`; seats unchanged |
| 2.4 report recovery | `recover_reports(from=1, count=1)` | original report 1 (same id and sequence), then `SequenceControl(next)` |
| 2.5 stale version | envelope with a lower version | `rejected stale_session`; nothing published |
| 2.8 recovery limits | `count=1001` / unretained range | `rejected recovery_limit` / `rejected recovery_out_of_range` |
| 3.2 / 3.3 races | two operations on one mission | the first registered wins; the loser's report has `mission_sequence=None` and `after_mission_sequence` = the winner's number |
| 3.6 replay | `recover_reports` | `get_history` unchanged; no new `mission_sequence` |

The integration tests named in plan.md own these checks.
