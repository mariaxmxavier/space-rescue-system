# Tasks: Clear and Ordered Communication

**Input**: `plan.md`, `spec.md` (user stories US1-US4), `data-model.md`, `contracts/`, `research.md` (P1-P12), `quickstart.md`, `design-diagrams.md`

**Tests**: included. FR-010 requires automated checks and 100% communication coverage, and the plan delivers test-first. Each model or rule task writes its test first (red), then the code (green), following superpowers:test-driven-development.

**Organization**: by user story, after Setup and Foundational. US1 is the MVP. US2 builds on US1's extracted classification. US3 verifies the mission order that US2's reports carry. US4 makes the package explainable and closes the architecture checks. The "Dispatch batches" section gives the exact order for parallel subagents.

## Format: `- [ ] TID [P?] [Story?] Description with path`

- **[P]**: different files and no dependency on an unfinished task. Dispatch these to parallel subagents in the same batch.
- **[Story]**: US1-US4, only in story phases.
- Every task names its owned files. Two `[P]` tasks in one batch never share a file (constitution, Development Workflow; research P12).
- No task commits (AGENTS.md section 8). The controller runs `make check-all` after every batch.

## Path conventions

- `C` = `rescue/communication/`; models under `C/models/<group>/`, rules under `C/rules/`.
- Unit tests: `tests/unit/communication/models/`, `tests/unit/communication/rules/`.
- Integration tests: `tests/integration/application/communication/`, `tests/integration/application/concurrency/`, `tests/integration/experiments/session_copy/`.
- Architecture tests: `tests/architecture/communication_layout/`.
- Diagrams: `docs/architecture/diagrams/rescue-domain-model/`.
- Docstring format: `contracts/maintainability.md`, section Explanations. Every module, class and public callable carries `What:`, `When called:`, `Why:` and `Diagram:` (both Communication `.mmd` paths). Private helpers carry `What:` and `Why:`.

---

## Phase 1: Setup

**Purpose**: capture the baseline that proves unsequenced behaviour does not change.

- [ ] T001 Run `make install` then `make check-all` on the clean checkout and record the result in the ledger. Save the demo output with `uv run python -m rescue.demo > <scratchpad>/demo-before.txt`.

---

## Phase 2: Foundational (blocks all user stories)

**Purpose**: turn the module into packages, add the closed vocabularies and the moved private helpers, and put the import rules and architecture tests in place.

**Checkpoint**: `make check-all` is green. The architecture tests exist and are `xfail(strict=True)`.

- [ ] T002 Move `rescue/communication/models.py` to `rescue/communication/models/_legacy.py` with `git mv`. The code moves unchanged. Create `C/models/__init__.py`, which re-exports `CommunicationMessage` and `MessageDelivery` from `_legacy` and sets `__all__`. Create docstring-only `__init__.py` files, with the four labels, in `C/models/vocabulary/`, `C/models/messages/`, `C/models/deliveries/`, `C/models/sessions/` and `C/models/recovery/`. Constraint: `from rescue.communication.models import CommunicationMessage, MessageDelivery` keeps working. Depends on T001.
- [ ] T003 Create `C/rules/__init__.py` (four-label docstring, `__all__ = []`). Depends on T002.
- [ ] T004 [P] Write `tests/unit/communication/models/test_delivery_disposition.py` first (red), then `C/models/vocabulary/delivery_disposition.py` (`DeliveryDisposition`, `StrEnum`). Constraint: values exactly `applied, ignored, lost, rejected, late`. Test that `DeliveryDisposition("lost") is DeliveryDisposition.LOST`, that an unknown value raises `ValueError`, and that `DeliveryDisposition.LOST == "lost"`.
- [ ] T005 [P] Write `tests/unit/communication/models/test_delivery_reason.py` first, then `C/models/vocabulary/delivery_reason.py` (`DeliveryReason`, `StrEnum`). Constraint: values exactly `response_applied, identity_conflict, transport_loss, unknown_request, invalid_input, closed_request, deadline_expired, unknown_mission, unknown_ship, insufficient_demand, insufficient_capacity, unavailable, expired_quote, revision_conflict, duplicate_sequence`.
- [ ] T006 [P] Write `tests/unit/communication/models/test_flow_direction.py` first, then `C/models/vocabulary/flow_direction.py` (`FlowDirection`, `StrEnum`). Constraint: values exactly `inbound, outbound`.
- [ ] T007 [P] Write `tests/unit/communication/models/test_recovery_rejection.py` first, then `C/models/vocabulary/recovery_rejection.py` (`RecoveryRejection`, `StrEnum`). Constraint: values exactly `stale_session, recovery_out_of_range, recovery_limit, recovery_in_progress, sequence_rewind`.
- [ ] T008 [P] Create `C/models/_validation.py` (private; What and Why docstrings). Move `_normalize_kind`, `_normalize_payload`, `_is_primitive` and the `Payload`/`PayloadValue` aliases from `_legacy.py` unchanged, keeping every error message. Expose them without the leading underscore inside this private module. Leave `_legacy.py` untouched until T018.
- [ ] T009 [P] Edit `pyproject.toml`: add `communication-isolated` (forbidden) and `communication-layers` (layers) exactly as in `contracts/import-contracts.md`, after the mission contracts. Keep every existing contract.
- [ ] T010 [P] Create `tests/architecture/communication_layout/test_one_public_name_per_file.py`. It walks `rescue/communication/**/*.py` with `ast`. Each module that is not `__init__` and has no leading underscore must define exactly one public top-level class or function. `rescue.communication.models.__all__` and `rescue.communication.rules.__all__` must equal the sets in `contracts/public-imports.md`. Mark it `@pytest.mark.xfail(strict=True, reason="until T034")`.
- [ ] T011 [P] Create `tests/architecture/communication_layout/test_docstrings.py`. Every module, class and public function in `rescue/communication/` has `What:`, `When called:`, `Why:` and `Diagram:`. Private helpers have `What:` and `Why:`. Every `Diagram:` path exists. Mark it `xfail(strict=True, reason="until T034")`.
- [ ] T012 [P] Create `tests/architecture/communication_layout/test_diagrams_match_code.py`. Parse the Communication class `.mmd` and ER `.mmd`, plus `class-diagrams/scenario-model.mmd` and `entity-relationship-diagrams/scenario-model-er.mmd`. For each communication class drawn in the class diagrams, its fields equal the dataclass fields in code. For each entity drawn in the ER diagrams, its attributes are persisted fields of that class (data-model.md, Diagram deltas). Mark it `xfail(strict=True, reason="until T050")`.

---

## Phase 3: User Story 1 - Process responses safely (Priority: P1) 🎯 MVP

**Goal**: delivery classification is a pure, named rule; `record_response` only gathers facts and applies the decision; outcomes are unchanged.

**Independent Test**: `uv run pytest tests/unit/communication tests/integration/application/communication -q`. The existing `test_communication.py` passes unedited, and the demo output is identical.

- [ ] T013 [P] [US1] Create `C/models/messages/communication_message.py` (`CommunicationMessage`, moved from `_legacy.py` and using `_validation`) and `tests/unit/communication/models/test_communication_message.py`. Constraints: `message_id`, `correlation_id` and `request_id` are non-blank Ids; `kind` is a non-blank str; `payload` is a tuple of primitive key/value pairs, where a str or bytes payload, a non-pair entry or a non-finite Decimal is rejected; `sent_at` is normalised. Keep every error message.
- [ ] T014 [P] [US1] Create `C/models/deliveries/message_delivery.py` (`MessageDelivery`, moved) and `tests/unit/communication/models/test_message_delivery.py`.
  - `disposition` becomes a `DeliveryDisposition` and `reason` a `DeliveryReason`. Each accepts the enum or its string value; an unknown value raises `DomainValidationError`.
  - Unchanged: "`received_at` is `None` exactly when disposition is `lost`"; a lost delivery cannot report an RTT; `attempt_number` > 0.
- [ ] T015 [P] [US1] Create `C/models/deliveries/delivery_facts.py` (`DeliveryFacts`) and `tests/unit/communication/models/test_delivery_facts.py`.
  - The fields are exactly those in data-model.md.
  - The seven flags must be `bool` (reject ints); instants are normalised; `received_at`, `submitted_at` and `deadline` may be `None`.
  - `request_open` and `request_expired` cannot both be true.
  - When `request_known` is false, `request_open` and `request_expired` are false.
- [ ] T016 [P] [US1] Create `C/models/deliveries/delivery_decision.py` (`DeliveryDecision`) and `tests/unit/communication/models/test_delivery_decision.py`. Constraints:
  - `action` is in `{"none", "record", "expire_then_record", "apply"}`.
  - `disposition` and `reason` are `None` exactly when `action == "none"`.
  - `result_status` is in `{"applied", "ignored", "rejected"}`.
  - `result_reason` is `None` or a `DeliveryReason` value or `late`.
- [ ] T017 [US1] Write `tests/unit/communication/rules/test_classify_delivery.py` first (one test per row), then `C/rules/classify_delivery.py` (`classify_delivery(facts: DeliveryFacts) -> DeliveryDecision`). Rows follow research P6; the first match wins. Receipt before send stays a boundary validation in central and is not a row.

  | Row | Facts | action | disposition / reason | result_status / result_reason |
  | --- | --- | --- | --- | --- |
  | 1 | delivery known and identical | `none` | — | `ignored` / None |
  | 2 | delivery known and different | `none` | — | `rejected` / `identity_conflict` |
  | 4 | message conflicts | `record` | `rejected` / `identity_conflict` | `rejected` / `identity_conflict` |
  | 5a | request unknown, no receipt | `record` | `lost` / `transport_loss` | `applied` / None |
  | 5b | request unknown, received | `record` | `ignored` / `unknown_request` | `ignored` / `unknown_request` |
  | 6 | `sent_at < submitted_at` | `record` | `rejected` / `invalid_input` | `rejected` / `invalid_input` |
  | 7 | no receipt | `record` | `lost` / `transport_loss` | `applied` / None |
  | 8a | closed, expired, deadline set and `received_at >= deadline` | `record` | `late` / `deadline_expired` | `ignored` / `late` |
  | 8b | closed, otherwise | `record` | `ignored` / `closed_request` | `ignored` / `closed_request` |
  | 9 | open, deadline set and `received_at >= deadline` | `expire_then_record` | `late` / `deadline_expired` | `ignored` / `late` |
  | 11 | otherwise | `apply` | `applied` / `response_applied` | `applied` / None |

  Row 10 (the mission rule raises) belongs to central, not this rule. Depends on T004, T005, T015, T016.
- [ ] T018 [US1] Point `C/models/__init__.py` at the new files: `CommunicationMessage`, `MessageDelivery`, `DeliveryFacts`, `DeliveryDecision` and the 4 vocabularies. Delete `C/models/_legacy.py`. Set `C/rules/__init__.py` to export `classify_delivery`. Depends on T008, T013-T017.
- [ ] T019 [US1] Refactor `RescueCentral.record_response` in `rescue/application/central.py`.
  - Keep in central: normalisation, the receipt-before-send check and request lookup.
  - Build `DeliveryFacts` from the indices and the mission, call `classify_delivery`, then execute its `action`:
    - `none`: publish nothing.
    - `record`: publish the delivery.
    - `expire_then_record`: `apply_outcome(EXPIRED, reason "response_deadline_reached")`, then record.
    - `apply`: `apply_outcome`. If it raises `DomainValidationError` or `TypeError`, record `rejected` with `_reason(error)` (row 10).
  - Remove the inline precedence branches.
  - Constraints: `tests/integration/application/communication/test_communication.py` passes unedited; the demo output equals T001's. Depends on T018.
- [ ] T020 [P] [US1] Create `tests/integration/application/communication/test_delivery_outcomes.py`. Through `new_run` and `RescueCentral`, write one test per row of the T017 table plus row 10. Each test asserts the `Result` status and reason, the recorded delivery's disposition and reason (or no record), and the mission's confirmed and pending seats. Also cover spec Story 1 scenarios 1-4 and the edge cases: a reused delivery identity conflicts with the same message id; receipt exactly at the deadline is late; a new attempt for an already applied message changes no seats. It must pass before and after T019. Depends on T001.

**Checkpoint**: US1 is complete. Classification is pure and tested row by row; behaviour and the demo are unchanged.

---

## Phase 4: User Story 2 - Sequence and recover messages (Priority: P1)

**Goal**: per-session idempotent inbound numbering with `NotApplied` gaps; recoverable outbound decision reports; controls; copies continue counters.

**Independent Test**: `uv run pytest tests/unit/communication tests/integration/application/communication/test_sessions.py tests/integration/application/communication/test_recovery.py tests/integration/application/concurrency/test_session_concurrency.py tests/integration/experiments/session_copy -q`

- [ ] T021 [P] [US2] Create `C/models/sessions/session_envelope.py` (`SessionEnvelope`) and `tests/unit/communication/models/test_session_envelope.py`. Constraints: `session_id` is a non-blank Id; `version` > 0; `direction` is a `FlowDirection`; `sequence` > 0; booleans are rejected as integers.
- [ ] T022 [P] [US2] Create `C/models/sessions/not_applied.py` (`NotApplied`) and `tests/unit/communication/models/test_not_applied.py`. Constraints: `session_id` is a non-blank Id; `version` > 0; `from_sequence` > 0; `count` > 0.
- [ ] T023 [P] [US2] Create `C/models/recovery/recovery_request.py` (`RecoveryRequest`) and `tests/unit/communication/models/test_recovery_request.py`. Constraints: `session_id` is a non-blank Id; `version` > 0; `from_sequence` > 0; `count` is any int, because the 1..1000 bound is checked by `recover_reports` so an out-of-bound request can be represented and rejected.
- [ ] T024 [P] [US2] Create `C/models/recovery/sequence_control.py` (`SequenceControl`) and `tests/unit/communication/models/test_sequence_control.py`. Constraints: `session_id` is a non-blank Id; `version` > 0; `direction` is a `FlowDirection`; `next_sequence` > 0.
- [ ] T025 [P] [US2] Create `C/models/recovery/decision_report.py` (`DecisionReport`) and `tests/unit/communication/models/test_decision_report.py`. Constraints:
  - `report_id`, `message_id` and `delivery_id` are non-blank Ids; `mission_id` is `Id | None`.
  - `envelope.direction` is `outbound`.
  - `disposition` and `reason` are vocabularies; `disposition` is never `lost`.
  - `after_mission_sequence` >= 0.
  - `mission_sequence` is `None` or `after_mission_sequence + 1`.
  - `mission_id is None` implies both mission fields are `None` / 0.

  Depends on T021.
- [ ] T026 [P] [US2] Add `envelope: SessionEnvelope | None` (kw-only, default `None`) to `C/models/deliveries/message_delivery.py` and extend `tests/unit/communication/models/test_message_delivery.py`. Constraints: `None` when the disposition is `lost`; when set, its direction is `inbound`. Depends on T014, T021.
- [ ] T027 [P] [US2] Create `C/models/sessions/communication_session.py` (`CommunicationSession`) and `tests/unit/communication/models/test_communication_session.py`. Constraints:
  - `session_id` is a non-blank Id; `version` > 0; `next_inbound` >= 1; `next_outbound` >= 1.
  - `reports` is a tuple whose outbound sequences are exactly `1..next_outbound-1`, in order, and whose session id and version equal the session's.
  - `gaps` is a tuple of `NotApplied` with the same session id and version.
  - `outstanding_recovery` is `None` or a `RecoveryRequest` with the same session id and version.

  Depends on T022, T023, T025.
- [ ] T028 [P] [US2] Create `C/models/recovery/report_cursor.py` (`ReportCursor`) and `tests/unit/communication/models/test_report_cursor.py`. Constraints: `session_id` is a non-blank Id; `version` > 0; `next_expected` >= 1; `buffered` is a tuple of `DecisionReport` sorted by sequence, with no duplicates, every sequence > `next_expected`, and the same session and version. Depends on T025.
- [ ] T029 [P] [US2] Write `tests/unit/communication/rules/test_accept_inbound.py` first, then `C/rules/accept_inbound.py`: `accept_inbound(session: CommunicationSession | None, envelope: SessionEnvelope) -> tuple[CommunicationSession | None, NotApplied | None, str]`. The verdict is in `{"execute", "duplicate", "stale"}`. Rows, from the data-model.md state table:
  - `None` session: create at the envelope's version with both counters at 1, then apply the envelope.
  - Higher version: reset counters, reports, gaps and outstanding.
  - Lower version: `stale`, session returned unchanged.
  - `n == expected`: `expected = n + 1`.
  - `n > expected`: `NotApplied(expected, n - expected)`, `expected = n + 1`.
  - `n < expected`: `duplicate`, unchanged.
  - An `outbound` envelope raises `DomainValidationError`.

  Depends on T027.
- [ ] T030 [P] [US2] Write `tests/unit/communication/rules/test_issue_report.py` first, then `C/rules/issue_report.py`: `issue_report(session, *, report_id, message_id, delivery_id, mission_id, disposition, reason, mission_sequence, after_mission_sequence) -> tuple[CommunicationSession, DecisionReport]`. The report envelope is `(session, version, outbound, next_outbound)`; the report is appended and `next_outbound` incremented. Test that two issues give sequences 1 and 2 and that the input session is unchanged. Depends on T027.
- [ ] T031 [P] [US2] Write `tests/unit/communication/rules/test_recover_reports.py` first, then `C/rules/recover_reports.py`: `recover_reports(session, request: RecoveryRequest) -> tuple[DecisionReport | SequenceControl, ...] | RecoveryRejection`. Checks in order, first match wins:
  1. `request.version != session.version`: `stale_session`.
  2. `session.outstanding_recovery is not None`: `recovery_in_progress`.
  3. `count < 1 or count > 1000`: `recovery_limit`.
  4. `from_sequence + count - 1 > next_outbound - 1`: `recovery_out_of_range`.
  5. Otherwise: the original report objects for the range, in order, then `SequenceControl(session, version, outbound, next_outbound)`.

  Test identity: `returned[i] is session.reports[j]`. Test the 1000 and 1001 boundaries. Depends on T027.
- [ ] T032 [P] [US2] Write `tests/unit/communication/rules/test_synchronise_inbound.py` first, then `C/rules/synchronise_inbound.py`: `synchronise_inbound(session, control: SequenceControl) -> tuple[CommunicationSession, NotApplied | None] | RecoveryRejection`.
  - Version mismatch: `stale_session`.
  - An outbound control raises `DomainValidationError`.
  - `next > expected`: `NotApplied(expected, next - expected)`, `expected = next`.
  - `next == expected`: unchanged, `None`.
  - `next < expected`: `sequence_rewind`.

  Depends on T027.
- [ ] T033 [P] [US2] Write `tests/unit/communication/rules/test_receive_report.py` first, then `C/rules/receive_report.py`: `receive_report(cursor, report) -> tuple[ReportCursor, tuple[DecisionReport, ...], tuple[int, int] | None]`.
  - Report == expected: deliver it, then drain consecutive buffered reports.
  - Report > expected: buffer it; return the gap `(expected, report - expected)`, counting only reports neither delivered nor buffered.
  - Report < expected, or already buffered: no effect.

  Test the spec's worked example: report 2 is buffered, report 1 arrives, both are delivered in order, and `next_expected` becomes 3. Depends on T028.
- [ ] T034 [US2] Export the 7 new models in `C/models/__init__.py` and the 5 new rules in `C/rules/__init__.py`, matching `contracts/public-imports.md` exactly. Remove the `xfail` from `test_one_public_name_per_file.py` and `test_docstrings.py`, and fix any docstring or layout failure they report in `rescue/communication/**`. Depends on T021-T033.
- [ ] T035 [P] [US2] Edit `rescue/application/contracts.py`:
  - `RecordResponse` gains `envelope: SessionEnvelope | None = None`.
  - New frozen commands `RecoverReports(session_id, version, from_sequence, count)` and `SynchroniseInbound(session_id, version, next_sequence)`.
  - `ErrorReason` gains `duplicate_sequence, stale_session, sequence_rewind, recovery_out_of_range, recovery_limit, recovery_in_progress, unknown_session`.

  Extend `tests/unit/application/contracts/` with a test that each new reason is accepted by `Result`. Depends on T034.
- [ ] T036 [P] [US2] Edit `rescue/application/state.py`: add `session_index: tuple[CommunicationSession, ...] = ()`. Constraints: every element is a `CommunicationSession`, session ids are unique within the run, and the index is deeply immutable. Add a test in `tests/unit/application/state/test_session_index.py`. Depends on T034.
- [ ] T037 [US2] Edit `rescue/application/central.py` (research P3, P5-P8; contracts/application-api.md).
  - **Session step in `record_response`**: runs only for a received delivery, after rows 1-2.
    - Use the envelope, or the default `SessionEnvelope("local:<ship_id>" or "local:unknown", 1, inbound, session.next_inbound)`.
    - Call `accept_inbound`. `stale`: return `rejected stale_session` and publish nothing. `duplicate`: record the delivery `ignored duplicate_sequence`, return `ignored duplicate_sequence`, and issue no report.
    - Otherwise continue with the US1 flow. The delivery stores its envelope.
  - **Reports**: after every recorded received delivery, call `issue_report`:
    - `after_mission_sequence` = the mission's last history `mission_sequence` before the decision (0 if none, or when the request is unknown);
    - `mission_sequence` = the new last entry's number when the decision appended history, else `None`.
  - Lost deliveries change no session and issue no report.
  - Publish the session, delivery, mission and report in the same returned `RunState`.
  - **New methods**:
    - `recover_reports(RecoverReports)`: read-only; maps `RecoveryRejection` to the same-named `ErrorReason`.
    - `synchronise_inbound(SynchroniseInbound)`.
    - `get_session(session_id)`: `rejected unknown_session` when the session is absent.
  - Constraint: T019's constraints still hold.

  Depends on T035, T036.
- [ ] T038 [P] [US2] Edit `rescue/experiments/models.py`: `RunBaseline` and `RunSnapshot` gain `session_index: tuple[object, ...] = ()`, validated like `message_index`. Edit `rescue/experiments/runner.py`: copy `session_index` in `install_baseline` and into the final snapshot, next to `message_index`. Constraint: a baseline built without `session_index` still works. Depends on T036.
- [ ] T039 [P] [US2] Create `tests/integration/application/communication/test_sessions.py`, covering:
  - Story 2.1 (both directions start at 1, independent counters);
  - 2.2 (inbound 3 while expecting 2 gives `NotApplied(2,1)`, message 3 is processed, expected becomes 4);
  - 2.3 (fresh-sequence retry confirms once; a delayed below-expected message is `ignored duplicate_sequence` with no seat change);
  - 2.5 (resume keeps counters; a higher version resets; a lower version is `rejected stale_session` with nothing published);
  - 2.6 (receipt before send publishes no session change; controls consume no business number);
  - the edge case "a lost inbound send does not advance the expected number".

  Assert `get_session` diagnostics: session, version, both counters, gaps and reports. Depends on T037.
- [ ] T040 [P] [US2] Create `tests/integration/application/communication/test_recovery.py`, covering:
  - Story 2.4: originals replayed with the same `report_id` and sequence, then `SequenceControl`; mission history and seats unchanged.
  - 2.8: `count=1001` gives `recovery_limit`; a range beyond retained gives `recovery_out_of_range`; an inactive version gives `stale_session`. Each is rejected with no state change.
  - `synchronise_inbound` advance (records `NotApplied`), equal (no-op) and rewind (`sequence_rewind`).

  Use `ReportCursor` and `receive_report` to replay the ship-side worked example from `docs/architecture/communication-ordering.md`. Depends on T037.
- [ ] T041 [P] [US2] Create `tests/integration/application/concurrency/test_session_concurrency.py` (Story 2.7). Threads from 2+ explicit sessions confirm against one mission's shared seats at the same time. Assert that confirmed + pending <= demand, that each session's counters are 1..N with no cross-session effect, and that no confirmation counts twice. Depends on T037.
- [ ] T042 [P] [US2] Create `tests/integration/experiments/session_copy/test_session_copy.py` (FR-007, FR-014):
  - A run copied from a baseline with sessions continues their counters and reports.
  - The source baseline is unchanged after the copy runs.
  - Two independent runs keep separate sessions.
  - A baseline without `session_index` runs and starts default sessions at 1.

  Depends on T037, T038.

**Checkpoint**: US2 is complete. Gaps are explicit, retries confirm once, replay preserves identity and copies continue; US1 tests are still green.

---

## Phase 5: User Story 3 - Order competing decisions per mission (Priority: P1)

**Goal**: prove the per-mission FIFO order. The mechanism is the existing `mission_sequence` (research P1), surfaced on reports by T037, so this story is verification.

**Independent Test**: `uv run pytest tests/integration/application/communication/test_mission_order.py tests/integration/application/concurrency/test_mission_order_concurrency.py -q`

- [ ] T043 [P] [US3] Create `tests/integration/application/communication/test_mission_order.py`, covering:
  - Story 3.1: the first decision is 1, then +1 with no gaps.
  - 3.2: two responses for one mission take effect in call order whatever their `sent_at` and session numbers.
  - 3.3: the worked example in `docs/architecture/communication-ordering.md`. The cancellation is 4; the late confirmation is `ignored closed_request`, its report has `mission_sequence=None` and `after_mission_sequence=4`, and seats stay 4.
  - 3.5: a retried message gets a new place and keeps its `message_id`.
  - 3.6: replay, an exact duplicate and a rejected input add no number.
  - 3.7: rebuild one mission's history from reports across two sessions and detect a removed report as a gap in `mission_sequence`.
  - SC-006: run each race fixture 20 times and assert identical numbers and seats.
  - SC-007: per mission, numbers are 1..N with no gaps.

  Depends on T037.
- [ ] T044 [P] [US3] Create `tests/integration/application/concurrency/test_mission_order_concurrency.py`, covering:
  - Story 3.4: threads act on two missions at once; each mission's history numbers are 1..N and independent.
  - Threads on one mission produce gapless numbers matching the commit order seen in history.

  Depends on T037.

**Checkpoint**: US3 is complete. Every race and gapless criterion has an executable check.

---

## Phase 6: User Story 4 - Understand and maintain communication (Priority: P2)

**Goal**: an overview that answers the contract's six questions, plus diagrams that match the code and are checked by tests.

**Independent Test**: `uv run pytest tests/architecture/communication_layout -q` with no `xfail` left; trace one response through the overview, rule, model and both diagrams.

- [ ] T045 [P] [US4] Write the `rescue/communication/__init__.py` module docstring. It answers the 6 overview questions in `contracts/maintainability.md`, each in 1-3 sentences, with the four labels. No code. Depends on T034.
- [ ] T046 [P] [US4] Update `docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd` and re-render its `.svg` with the command in the diagram README. Per data-model.md (Diagram deltas):
  - add `request_id` to the message;
  - add `communication_rtt_seconds` and `envelope` to the delivery;
  - add the 4 enums and the 7 new classes;
  - add the 6 rules as `<<function>>` classes;
  - show the session owning its reports and gaps;
  - add a note linking the report to `RequestHistoryEntry.mission_sequence`.

  Keep the existing front-matter config. Depends on T037.
- [ ] T047 [P] [US4] Update `.../namespaces/Communication/entity-relationship-diagram.mmd` and its `.svg`:
  - change the title to Communication;
  - add `COMMUNICATION_SESSION`, `DECISION_REPORT` and `NOT_APPLIED`;
  - give the delivery `session_id`, `version` and `sequence`;
  - add the report → history `mission_sequence` cross-reference.

  Only persisted concepts. Depends on T037.
- [ ] T048 [P] [US4] Update `docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd` and its `.svg` with the same communication classes, plus `RunBaseline.session_index`. Depends on T038.
- [ ] T049 [P] [US4] Update `docs/architecture/diagrams/rescue-domain-model/entity-relationship-diagrams/scenario-model-er.mmd` and its `.svg` with the same entities. Add one line to `docs/architecture/diagrams/rescue-domain-model/README.md` naming the 007 changes. Depends on T038.
- [ ] T050 [US4] Remove the `xfail` from `tests/architecture/communication_layout/test_diagrams_match_code.py`. Fix any mismatch it reports in the four `.mmd` files only, re-rendering each changed `.svg`. Depends on T045-T049.

**Checkpoint**: US4 is complete. Every architecture test passes without `xfail`.

---

## Phase 7: Polish & verification

- [ ] T051 Edit `Makefile`: the `rescue/communication` coverage line gains `--fail-under=100`. Run `make test`; for any uncovered line or branch, add a unit test in `tests/unit/communication/**`. Change no production code unless a branch is unreachable, in which case remove that branch and record why in the ledger. Depends on T050.
- [ ] T052 [P] Update `README.md` near the "in-memory adapter serializes" and "Response identity" paragraphs with 4-6 sentences:
  - default and explicit sessions;
  - gap notices;
  - report recovery;
  - per-mission order by lock registration (research P2);
  - why timestamps never reorder decisions.

  Link `docs/architecture/communication-ordering.md`. Depends on T050.
- [ ] T053 [P] Update `docs/architecture/communication-ordering.md`: the implementation status becomes "implemented on branch `007-communication-conformance`", the code trace table names the real files, and the line saying the diagrams represent the pre-007 implementation is removed. Update the 007 status in `docs/planning/roadmap.md` to "Implemented; awaiting merge". Depends on T050.
- [ ] T054 Verify: `make check-all` is green; `uv run python -m rescue.demo` matches `<scratchpad>/demo-before.txt`; walk through `quickstart.md` steps 3-7, including the temporary boundary break and its revert. Record the results in the ledger. Depends on T051-T053.

---

## Dependencies & Execution Order

### Phase dependencies

- Setup (T001) comes first.
- Foundational (T002-T012) blocks every story.
- US1 (T013-T020) is next: it extracts the classification that US2's `record_response` builds on.
- US2 (T021-T042) needs US1's T019, because the session step wraps the classified flow.
- US3 (T043-T044) needs T037, which surfaces mission numbers on reports.
- US4 (T045-T050) needs T034 (overview) and T037/T038 (final fields for diagrams).
- Polish (T051-T054) comes last.

### Story independence

- US1 delivers value alone: a pure rule, identical behaviour.
- US2 and US3 each have their own test files and can be validated alone once their dependencies are done.
- US3 adds no production code; if US2's T037 regresses mission numbering, only US3's tests catch it.
- US4 changes no behaviour.

### Within each task

The test is written first and must fail for the right reason. Then the code is written and the test passes. The gate runs at the end of the batch.

## Dispatch batches (multi-agent)

The controller dispatches each batch, waits for every report and task review, then runs `make check-all` before the next batch. `[P]` batches run as parallel subagents in the same checkout, with disjoint files.

| Batch | Tasks | Parallel | Model tier |
|-------|-------|----------|------------|
| B1 | T001 | no | controller |
| B2 | T002, then T003 | no | cheap |
| B3 | T004, T005, T006, T007, T008, T009, T010, T011, T012 | **[P] ×9** | cheap (T010-T012 standard) |
| B4 | T013, T014, T015, T016, T020 | **[P] ×5** | cheap (T020 standard) |
| B5 | T017 | no | standard |
| B6 | T018 | no | cheap |
| B7 | T019 | no | standard |
| B8 | T021, T022, T023, T024 | **[P] ×4** | cheap |
| B9 | T025, T026 | **[P] ×2** | cheap |
| B10 | T027, T028 | **[P] ×2** | standard |
| B11 | T029, T030, T031, T032, T033 | **[P] ×5** | standard |
| B12 | T034 | no | standard |
| B13 | T035, T036 | **[P] ×2** | cheap |
| B14 | T037, T038 | **[P] ×2** | most capable (T037), cheap (T038) |
| B15 | T039, T040, T041, T042, T043, T044, T045, T046, T047, T048, T049 | **[P] ×11** | standard |
| B16 | T050 | no | standard |
| B17 | T051, T052, T053 | **[P] ×3** | standard (T051), cheap |
| B18 | T054 | no | controller, then the final whole-branch review on the most capable model |

These batches refine the plan's waves: models that depend on `SessionEnvelope` and `DecisionReport` need their own batches (B8-B10).

## Parallel execution examples

```text
# B3, Foundational: nine subagents, nine disjoint file sets
Task: "T004 DeliveryDisposition + test"     Task: "T005 DeliveryReason + test"
Task: "T006 FlowDirection + test"           Task: "T007 RecoveryRejection + test"
Task: "T008 _validation.py"                 Task: "T009 pyproject.toml contracts"
Task: "T010 layout test (xfail)"            Task: "T011 docstring test (xfail)"
Task: "T012 diagram test (xfail)"

# B11, US2 rules: five subagents, one rule file + one test file each
Task: "T029 accept_inbound"   Task: "T030 issue_report"   Task: "T031 recover_reports"
Task: "T032 synchronise_inbound"   Task: "T033 receive_report"

# B15, tests, overview and diagrams: eleven subagents
Task: "T039 test_sessions"  Task: "T040 test_recovery"  Task: "T041 session concurrency"
Task: "T042 session copy"   Task: "T043 mission order"  Task: "T044 mission order concurrency"
Task: "T045 overview docstring"  Task: "T046 Communication class"  Task: "T047 Communication ER"
Task: "T048 scenario class"      Task: "T049 scenario ER + README note"
```

## Implementation strategy

### MVP first (User Story 1 only)

1. B1-B3: Setup and Foundational.
2. B4-B7: US1.
3. Stop and validate: `test_communication.py` is unedited and green, `test_delivery_outcomes.py` is green, and the demo is identical.

### Incremental delivery

1. US1: pure classification, no behaviour change.
2. US2: sessions, gaps and recovery; unsequenced calls still unchanged.
3. US3: mission order proven.
4. US4: diagrams and architecture checks closed.
5. Polish: 100% coverage gate, README and docs, final verification.

## Notes

- `[P]` tasks touch different files; no two `[P]` tasks in one batch share a file.
- Field constraints are quoted from data-model.md in each task; do not relax them during implementation.
- Never edit `.specify/bridge-snapshots/`. Never commit; the maintainer decides when.
