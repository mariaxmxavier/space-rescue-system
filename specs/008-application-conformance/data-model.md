# Data Model: A Clear Application Layer

Phase 1 for [plan.md](plan.md). This feature adds no new domain data. It moves and names the
existing application types and maps every file to a diagram element (FR-004). Line ranges refer to
`rescue/application/central.py` on `origin/main` at `ae38f1a`, after 003 and 007 merged. They were
measured on 2026-11-17 and must be re-checked if `main` moves before the wave that uses them.

Diagram shorthand: **APP-UML** =
`docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd`,
**APP-ER** = `.../namespaces/Application/entity-relationship-diagram.mmd`.

## 1. Data types

### RunState (`rescue/state/run_state.py`, moved from `application/state.py`)

| Field | Type | Rule |
|---|---|---|
| `application_run_id` | `Id` | nonblank (`normalize_id`) |
| `central_id` | `Id` | nonblank |
| `market` | `B3Market` | must be a `B3Market`; deeply immutable |
| `missions` | `tuple[Mission, ...]` | `Mission` values only; `mission_id` unique within the run |
| `command_index` | `tuple[(run_id, command_id, operation, payload, value), ...]` | deeply immutable; one entry per applied command; used for replay |
| `message_index` | `tuple[(CommunicationMessage, tuple[MessageDelivery, ...]), ...]` | deeply immutable |
| `delivery_index` | `tuple[(delivery_id, message_id, MessageDelivery), ...]` | deeply immutable |
| `decision_index` | `tuple[MobilisationDecision, ...]` | deeply immutable |
| `session_index` | `tuple[CommunicationSession, ...]` | new since 007; deeply immutable; one per ship session |
| `policies`, `scenarios`, `completed_runs` | `tuple[...]` | deeply immutable |

Behaviour: `mission(mission_id) -> Mission | None`. Construction rejects anything that is not
deeply immutable, using `rescue.values.is_deeply_immutable` (R6). Diagrams: APP-ER entity
`RunState` (1–1 `B3Market`, 1–N `Mission`, 1–N each index including `session_index`); APP-UML
class `RunState`.

### Result and vocabulary (`rescue/application/contracts/`)

| File | Definition | Rule | Diagram |
|---|---|---|---|
| `result.py` | `Result[T](status, value=None, reason=None)` | `status` ∈ `ResultStatus`; `reason` ∈ `ErrorReason` or `None` | APP-UML `Result` |
| `result_status.py` | `ResultStatus`: applied, replayed, rejected, ignored | closed set | APP-UML enum |
| `error_reason.py` | `ErrorReason`: 21 values in `contracts.py` from line 27, unchanged (7 were added by 007) | closed set | APP-UML enum |
| `snapshots.py` | the 8 `*Snapshot` aliases from `central.py` lines 81–88 (`MissionSnapshot = Mission`, …) | aliases only, no new types | APP-UML note |

Result transitions per call: a service returns exactly one of `applied` (state published),
`replayed` (same `command_id` and payload, original value, no state change), `rejected` (state
unchanged, `reason` set), or `ignored` (request already closed, `reason = closed_request`; or a
duplicate delivery, `reason = duplicate_sequence`). `record_response` may also return
`rejected/stale_session`.

## 2. Commands (`rescue/application/contracts/commands/`, one file each, fields unchanged)

Sixteen commands. The two added since 007 are `RecoverReports` (`contracts.py` line 148) and
`SynchroniseInbound` (line 165).

| File | Command | Used by service |
|---|---|---|
| `register_mission.py` | `RegisterMission` | `missions/register_mission` |
| `register_ship.py` | `RegisterShip` | `fleet/register_ship` |
| `publish_availability.py` | `PublishAvailability` | `fleet/publish_availability` |
| `publish_offer.py` | `PublishOffer` | `fleet/publish_offer` |
| `request_quotes.py` | `RequestQuotes` | `quotes/request_quotes` |
| `record_quote.py` | `RecordQuote` | `quotes/record_quote` |
| `accept_quote.py` | `AcceptQuote` | `quotes/accept_quote` |
| `reject_quote.py` | `RejectQuote` | `quotes/reject_quote` |
| `create_request.py` | `CreateRequest` | `requests/create_request` |
| `cancel_request.py` | `CancelRequest` | `requests/cancel_request` |
| `expire_request.py` | `ExpireRequest` | `requests/expire_request` |
| `record_response.py` | `RecordResponse` | `communication/record_response` |
| `recover_reports.py` | `RecoverReports` | `communication/recover_reports` |
| `synchronise_inbound.py` | `SynchroniseInbound` | `communication/synchronise_inbound` |
| `mobilise.py` | `Mobilise` | `mobilisation/mobilise` |
| `compare_policies.py` | `ComparePolicies` | `comparison/compare_policies` |

All are `@dataclass(frozen=True, slots=True)`, with field order and defaults unchanged, so
positional construction keeps working. APP-UML shows them as one `Commands` group, with a
dependency arrow from each service folder.

## 3. Services (`rescue/application/services/`, one function each)

Twenty-two services in seven folders. `get_session` takes a plain `session_id` and has no command.

| Folder / file | Function (keyword-only ports) | From `central.py` (lines) | Ports |
|---|---|---|---|
| `missions/register_mission.py` | `register_mission(command, *, store)` | 408–428 | store |
| `missions/get_progress.py` | `get_progress(mission_id, now, *, store)` | 1125–1137 | store |
| `missions/get_history.py` | `get_history(mission_id, *, store)` | 1138–1149 | store |
| `fleet/register_ship.py` | `register_ship(command, *, store)` | 429–441 | store |
| `fleet/publish_availability.py` | `publish_availability(command, *, store)` | 442–457 | store |
| `fleet/publish_offer.py` | `publish_offer(command, *, store)` | 458–498 | store |
| `quotes/request_quotes.py` | `request_quotes(command, *, store, id_source)` | 499–547 | store, ids |
| `quotes/record_quote.py` | `record_quote(command, *, store)` | 548–564 | store |
| `quotes/accept_quote.py` | `accept_quote(command, *, store, id_source)` | 565–625 | store, ids |
| `quotes/reject_quote.py` | `reject_quote(command, *, store)` | 642–658 | store |
| `quotes/expire_quotes.py` | `expire_quotes(now, *, store)` | 659–686 | store |
| `requests/create_request.py` | `create_request(command, *, store, id_source)` | 626–641 | store, ids |
| `requests/cancel_request.py` | `cancel_request(command, *, store, id_source)` | 687–695 | store, ids |
| `requests/expire_request.py` | `expire_request(command, *, store, id_source)` | 696–730 | store, ids |
| `communication/record_response.py` | `record_response(command, *, store, id_source)` | 765–1033 (269 lines: split, §4b) | store, ids |
| `communication/recover_reports.py` | `recover_reports(command, *, store)` | 1034–1071 | store |
| `communication/synchronise_inbound.py` | `synchronise_inbound(command, *, store)` | 1072–1104 | store |
| `communication/get_session.py` | `get_session(session_id, *, store)` | 1105–1124 | store |
| `communication/get_deliveries.py` | `get_deliveries(message_id, *, store)` | 1170–1186 | store |
| `mobilisation/mobilise.py` | `mobilise(command, *, store, id_source)` | 1250–1322 | store, ids |
| `mobilisation/get_decision.py` | `get_decision(decision_id, *, store)` | 1150–1169 | store |
| `comparison/compare_policies.py` | `compare_policies(command, *, store, id_source, simulator)` | 1187–1249 | store, ids, simulator |

`record_response` is the only service over 250 lines today. Its body contains a nested
`publish_delivery` closure and four outcome branches. The split in §4b keeps each file under 250
lines and keeps the behaviour the same.

## 4. Shared helpers (`rescue/application/shared/`)

### 4a. Helpers (15 files, one function each)

| File | Function | From `central.py` | Used by |
|---|---|---|---|
| `find_mission.py` | `find_mission(state, mission_id)` | `_mission` 91–95 | most services |
| `replace_mission.py` | `replace_mission(state, mission)` | `_set_mission` 96–106 | mutating services |
| `find_session.py` | `find_session(state, session_id)` | `_session` 107–113 | record_response, synchronise_inbound, get_session |
| `replace_session.py` | `replace_session(state, session)` | `_set_session` 114–128 | record_response, synchronise_inbound, recover_reports |
| `make_result.py` | `make_result(status, value=None, reason=None)` | `_result` 129–132 | all services |
| `error_reason_for.py` | `error_reason_for(error)` | `_reason` 133–155 | all services |
| `find_offer_revision.py` | `find_offer_revision(state, mission_id, ship_id, revision_id)` | `_offer_revision` 156–164 | publish_offer, open_request |
| `request_capacity_reason.py` | `request_capacity_reason(state, mission, ship_id, quantity, revision_id)` | `_request_capacity_reason` 165–210 | open_request |
| `find_quote.py` | `find_quote(state, quote_id)` | `_find_quote` 211–214 | accept_quote, reject_quote |
| `find_rfq.py` | `find_rfq(state, rfq_id)` | `_find_rfq` 215–218 | record_quote, accept_quote, open_request |
| `command_entry.py` | `command_entry(state, command_id)` | `_command_entry` 219–232 | accept_quote, open_request |
| `decision_link_reason.py` | `decision_link_reason(state, ...)` | `_decision_link_reason` 233–274 | open_request |
| `append_command.py` | `append_command(state, command_id, operation, payload, value)` | `_append_command` 275–284 | open_request |
| `open_request.py` | `open_request(state, *, id_source, command_id, ...)` | `_create_request` 285–400, without the `central` parameter | create_request, accept_quote |
| `close_pending_request.py` | `close_pending_request(state, mission_id, request_id, outcome, at, reason, *, id_source, guard=None)` | `_close_request` 731–764 merged with the `expire_request` body 696–730 | cancel_request, expire_request |

### 4b. Delivery steps (6 files in `shared/delivery/`, split from `record_response` 765–1033: 4 step functions, 2 data classes)

Folder `shared/delivery/`. The orchestrator stays in `communication/record_response.py` and keeps
the public signature.

| File | Function or type | Takes from the original body | Returns |
|---|---|---|---|
| `normalised_response.py` | `NormalisedResponse` (frozen dataclass; its own file, so each file holds one definition) | the return type of the next step | not a step |
| `normalise_response.py` | `normalise_response(command) -> NormalisedResponse` | the first `try` block: IDs, attempt, instants, RTT, confirmed seats, the receipt-before-send check, and the `CommunicationMessage` build | normalised fields and message |
| `delivery_context.py` | `DeliveryContext` (frozen dataclass) | the values the later steps read: message, IDs, attempt, instants, known delivery, existing message, mission, request, envelope and session | a value passed between steps |
| `classify_response.py` | `classify_response(state, normalised) -> (DeliveryContext, decision)` | the `known_delivery`, `existing_message`, `same_message`, `mission` and `request` lookups and the `classify_delivery(DeliveryFacts(...))` call | context and classification decision |
| `resolve_session.py` | `resolve_session(state, context, command) -> (DeliveryContext, Result or None)` (deviation: returns the rejection, so the orchestrator can return it) | the envelope default (`local:<ship>`), `accept_inbound`, and the `stale` verdict (returns `rejected/stale_session`) | context with session and verdict |
| `publish_delivery.py` | `publish_delivery(state, context, disposition, reason, *, keep_message=True, decided_mission=None, report=True) -> RunState` | the nested closure as a module function; writes the delivery indices and issues the report through `communication_rules.issue_report` | new state |

Behaviour: the four branches (duplicate, record, expire_then_record, apply_outcome) stay in
`record_response`. Each reaches `publish_delivery` with the same arguments as before.
`expire_then_record` still draws its event ID from `id_source`.

## 5. Ports (`rescue/adapters/ports/`)

| Port | Operations | Owner | Implementations |
|---|---|---|---|
| `TransactionStore` | `transact(operation)`, `snapshot()` | 003 (merged) | `MemoryTransactionStore` |
| `Clock` | `now()` | 003 (merged) | `ZeroClock` (held by the facade, used by no service today) |
| `IdSource` | `next_id(kind)` | 003 (merged) | `SequenceIdSource` |
| `Simulator` | `simulate(scenario, policy, simulation_id) -> RunSnapshot` | **008** (R4) | `RunnerSimulator` in `rescue/experiments/simulator.py` |

## 6. RescueCentral (facade, `rescue/application/central.py`)

Frozen dataclass fields: `application_run_id`, `central_id`, `store`, `clock`, `id_source`, and the
new last field `simulator: Simulator` (no default). `bootstrap.new_run` is the only constructor.

Twenty-two public methods, each with the same signature as today and a body of exactly
`return <service>(<args>, store=self.store, ...)`:

`register_mission`, `register_ship`, `publish_availability`, `publish_offer`, `request_quotes`,
`record_quote`, `accept_quote`, `create_request`, `reject_quote`, `expire_quotes`, `cancel_request`,
`expire_request`, `record_response`, `recover_reports`, `synchronise_inbound`, `get_session`,
`get_progress`, `get_history`, `get_decision`, `get_deliveries`, `compare`, `mobilise`.

The private method `_close_request` (731–764) is removed. The 8 snapshot aliases move to
`contracts/snapshots.py`. Diagram: APP-UML class `RescueCentral` with `<<facade>>` and one
dependency on each service package.

## 7. Validation rules carried over unchanged

- Identifiers are nonblank strings, quantities are exact positive ints and instants are finite,
  nonnegative `Decimal`s, all through `rescue.values`.
- Replay: the same `command_id` with the same payload returns `replayed` and the original value. A
  different payload returns `rejected/identity_conflict`.
- A request deadline must be after `now`, otherwise `rejected/invalid_input`.
- An expiry before the deadline returns `rejected/invalid_input`. A request that is already closed
  returns `ignored/closed_request`.
- A delivery whose attempt is already recorded returns `ignored/duplicate_sequence`. A session
  version older than the stored one returns `rejected/stale_session`.
- Any `DomainValidationError` or `TypeError` inside a transaction returns `rejected` with the
  reason from `error_reason_for` and publishes nothing.
