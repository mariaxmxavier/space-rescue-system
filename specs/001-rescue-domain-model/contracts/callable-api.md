# Callable application contract

Proposed Python interface; transport unspecified. No HTTP routes, wire server or database is required.

## Shared models

Use frozen dataclasses containing primitive values, tuples, enums and Decimal; mutable objects never cross the boundary. `Instant = Decimal`, `Id = str`. Input time normalization accepts int or decimal string, rejecting bool and floats; quantities accept only type(value) is int. Reject non-finite values before sorting or arithmetic.

`Result[T]` contains `status` (applied, replayed, rejected, ignored), `value: T | None`, `reason: str | None`. Error reasons: invalid_input, unknown_mission, unknown_ship, unknown_request, unknown_decision, unknown_message, identity_conflict, closed_request, late, insufficient_demand, insufficient_capacity, unavailable, expired_quote, revision_conflict. No partial business mutation on rejection. Getters return snapshots or unknown_* results.

Command dataclasses and method signatures live in `rescue/application/contracts.py`; central methods in `central.py`:

| Method | Input fields | Result value |
| --- | --- | --- |
| register_mission(command: RegisterMission) | mission_id, station_name, people_count, created_at | MissionSnapshot |
| register_ship(command: RegisterShip) | ship_id, name | ShipSnapshot |
| publish_availability(command: PublishAvailability) | ShipAvailability from data-model.md | AvailabilitySnapshot |
| publish_offer(command: PublishOffer) | offer_id, mission_id, ship_id, ShipOfferRevision | OfferSnapshot |
| request_quotes(command: RequestQuotes) | mission_id, now, response_deadline=None | tuple[RFQSnapshot, ...] |
| record_quote(command: RecordQuote) | RFQOffer from data-model.md, now | QuoteSnapshot |
| accept_quote(command: AcceptQuote) | command_id, mission_id, quote_id, response_deadline=None, decision_id=None, revision_id=None, now | RequestSnapshot |
| create_request(command: CreateRequest) | command_id, mission_id, ship_id, requested_seats, revision_id, response_deadline=None, decision_id=None, now | RequestSnapshot |
| reject_quote(command: RejectQuote) | quote_id, now | QuoteSnapshot |
| expire_quotes(now: Instant) | expire held quotes and unanswered RFQs whose deadlines are reached | tuple[Id, ...] |
| record_response(command: RecordResponse) | message_id, delivery_id, attempt_number, request_id, outcome, confirmed_seats, sent_at, received_at=None for loss, communication_rtt_seconds=None | RequestSnapshot or None for a recorded lost attempt |
| cancel_request(command: CancelRequest) | mission_id, request_id, now, reason | RequestSnapshot |
| expire_request(command: ExpireRequest) | mission_id, request_id, now | RequestSnapshot |
| get_progress(mission_id: Id, now: Instant) | mission key and observation instant | MissionProgress |
| get_history(mission_id: Id) | mission key | tuple[RequestHistoryEntry, ...] |
| mobilise(command: Mobilise) | mission_id, policy_id, policy_revision, now | DecisionSnapshot |
| get_decision(decision_id: Id) | decision key | DecisionSnapshot |
| get_deliveries(message_id: Id) | logical message key | tuple[MessageDelivery, ...] |
| compare(command: ComparePolicies) | scenario_id, scenario_revision, tuple of policy keys | tuple[RunSnapshot, ...] |

Each method returns Result[value type]. IDs for generated requests, events, RFQs, decisions, evaluations and runs come from IdSource.next_id(kind: str) -> str. Clock.now() -> Instant is supplied at the edge when a caller lacks time; domain code never reads the wall clock. Explicit command instants govern the operation. Mobilise records a proposed decision; caller submits resulting request/quote-accept commands, so quote acquisition and selection are not hidden side effects.

## Ports and pure functions

`TransactionStore.transact(operation: Callable[[RunState], tuple[RunState, T]]) -> T` executes against an immutable consistent RunState and publishes returned state under one lock; exception publishes nothing. RunState comprises central identity, mission registry, market, history, message/delivery indexes, command index, policy/scenario registries and completed experiment snapshots. Store read operations also use transact with unchanged state. Domain values live in their capability modules; RunState in application/state.py composes them.

Mission functions in mission/rules.py:
`register(data: MissionData) -> Mission`; `add_request(mission: Mission, request: SeatRequest, context: TransitionContext) -> Mission`; `apply_outcome(mission: Mission, request_id: str, outcome: str, confirmed: int, context: TransitionContext) -> Mission`; `progress(mission: Mission) -> MissionProgress`. Each applied mutation returns a new Mission with exactly one history entry; event identity/time are supplied through immutable transition metadata (include `event_id`, `at`, `reason`, `message_id=None` in a `TransitionContext` argument to add_request/apply_outcome). No adapter calls.
`timing(request: SeatRequest, now: Instant) -> RequestTiming` returns waiting seconds and optional response elapsed seconds without changing the request.

Market functions in market/rules.py:
`usage(market: B3Market, missions: tuple[Mission, ...], ship_id: str) -> ShipUsage`;
`hold_quote(market: B3Market, missions: tuple[Mission, ...], quote: RFQOffer, now: Instant) -> B3Market`;
`transfer_quote(market: B3Market, quote_id: str, request_id: str, now: Instant) -> B3Market`;
`close_quote(market: B3Market, quote_id: str, status: str, now: Instant) -> B3Market`.
Transfer is only called by the application transaction with successful Mission request creation. Validation of latest inventory and demand occurs before publication.

`select_offers(mission: Mission, candidates: tuple[Candidate, ...], policy: MobilisationPolicy, context: DecisionContext) -> MobilisationDecision` in mobilisation/policies.py. Candidate combines `ship_id`, immutable revision, market free seats and optional quote; the explicit ship ID enables deterministic tie-breaking because revisions do not contain their owning ship. DecisionContext supplies decision/evaluation IDs and time.

`simulate(scenario: RescueScenario, policy: MobilisationPolicy, run_id: str) -> RunSnapshot` in experiments/runner.py uses a fresh central context; `summarize(run: RunSnapshot) -> SimulationResult` in experiments/results.py. A scenario requires a finite positive event budget and immutable RunBaseline; response rules are finite `(ship_id, request_ordinal)` scripts. `summarize` consumes the stopped pre-result snapshot; `simulate` returns a finalized run with its result attached.

## Retry, response and ordering behavior

Request command key is (run_id, command_id); normalized payload includes operation kind, mission, ship, quantity, quote/revision/decision basis and deadline, but excludes retry observation now. Identical retry returns original request even if it has since closed or quote expired. Changed payload rejects before any new expiration or allocation side effect. Message key is (run_id, message_id); stable payload excludes delivery ID, attempt number, received_at and communication RTT. Exact duplicate is ignored, conflicting reuse is rejected. Each attempt gets its own delivery disposition; reject delivery ID reuse with changed data. A lost response has `received_at=None`, records `disposition="lost"` and does not change the request. Received responses may report the configured outbound-plus-return `communication_rtt_seconds`. Unknown request IDs produce diagnostics only.

After identity checks, expire pending requests if receipt >= deadline, then classify a response as late; otherwise a closed request is ignored with closed_request. First valid pre-deadline response wins; later competing messages cannot revise it. Reject invalid quantity/outcome combinations without changing accepted commitments. For a refused outcome confirmed_seats=0; partial requires 0<confirmed<requested; accepted requires equality.

No mutable registry escapes. Fresh bootstrap creates a new run ID and empty mission/history/command/message state. A comparison clones baseline values and never writes to the operational store.
