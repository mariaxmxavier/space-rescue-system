# Rescue data model architecture

Status: proposed implementation design for the draft [spec](spec.md). Existing ER/UML views remain the conceptual source; no diagram semantics or visibility approvals are changed here.

## Ownership and dependency direction

`rescue/mission/` owns Mission, SeatRequest, transitions, progress and applied history. `rescue/market/` owns ship availability, RFQs, holds and immutable offers. `rescue/mobilisation/` owns pure selection and explanations. `rescue/communication/` owns logical message and delivery values. `rescue/experiments/` owns scenario values and result calculation. These are proposed code boundaries chosen for policy ownership, not an inference that conceptual namespaces prescribe packages.

`rescue/application/central.py` owns RescueCentral orchestration; `ports.py` owns TransactionStore, Clock and IdSource protocols. Outer `adapters/memory.py` implements atomic run state; `bootstrap.py` constructs exactly one central per RunContext. No global singleton. Experiments create independent contexts. Domain imports only standard-library value helpers and other explicitly listed domain contracts; never application, adapters or bootstrap. Outer adapters depend inward. Return immutable snapshots, never internal mutable maps.

## Entity catalogue

All fields and associations below are retained from the specification. IDs are nonblank case-sensitive strings; quantities are strict integers (bool rejected); time values are finite Decimal seconds. Collections become immutable tuples at boundaries. Optional values use None, never fabricated zero timestamps.

| Concept | Meaning and fields | Relationships |
| --- | --- | --- |
| RescueCentral | UML proposes private `central_id` and `application_run_id`; both identify the one central within one run | Exactly one instance per run; registers zero or more missions in a registry looked up by `mission_id` and retains their in-memory state and existing request history for that run; coordinates mobilisation and outcomes, delegating request changes to Mission |
| Mission | UML proposes private `mission_id`, `station_name`, `people_count`, and `created_at`; ER shows the same data attributes without visibility; `people_count` is fixed after registration | Owns requests, their state transitions, mission invariants, and applied history; has calculated progress |
| Ship | UML proposes private `ship_id`, `name` | Has changing availability; B3Market accounts for holds and confirmed commitments across missions to prevent overbooking; fleet-wide optimisation is excluded |
| B3Market | `market_id` | Coordinates RFQs and tracks holds and confirmed commitments against ship availability across missions; does not optimise fleet allocation |
| ShipAvailability | `availability_id`, `ship_id`, `total_seats`, `arrival_estimate_seconds`, `available`, `recorded_at` | Time-specific capacity and arrival snapshot; the latest snapshot by `recorded_at` supplies the current seat limit; B3Market accounts active unaccepted holds, pending requests, and confirmed commitments against it, each once |
| SeatRFQ | `rfq_id`, `mission_id`, `ship_id`, `availability_id`, `requested_seats`, `status`, `sent_at`, optional `response_deadline` | One time-specific request addressed to one ship available for the mission when issued, against the referenced availability snapshot; receives zero or one RFQOffer response; B3Market sends one RFQ to each such available ship |
| ShipOffer | `offer_id`, `mission_id`, `ship_id` | One logical offer per ship and mission; has one or more revisions |
| ShipOfferRevision | `revision_id`, `revision_number`, `capacity`, `arrival_estimate_seconds`, `available`, `recorded_at` | Immutable revision of one offer; highest `revision_number` is current; `recorded_at` is metadata, not ordering; referenced by requests and evaluations |
| SeatRequest | `request_id`, `command_id`, `requested_seats`, `confirmed_seats`, `outcome`, `submitted_at`, optional `response_received_at`, optional `response_deadline`, optional `closed_at` | One mission and one ship; central acceptance of one RFQOffer creates a pending request for the full held quantity; ship response determines confirmed seats; retains the originating RFQOffer and, when used, the immutable ShipOfferRevision basis; optionally one originating decision. `command_id` is retained to recognize repeated request-creation commands; its scope, payload comparison, collision handling, and persistence are unspecified |
| RFQOffer | `offer_id`, `rfq_id`, `offered_seats`, `arrival_estimate_seconds`, `expires_at`, `recorded_at`, `status` | Response from the ship addressed by its SeatRFQ; offered seats do not exceed the RFQ quantity and are held against latest availability until acceptance, quote rejection, or expiry; acceptance transfers the full hold to one pending SeatRequest for ship confirmation. Expiry duration/policy unspecified |
| RequestHistoryEntry | `event_id`, `mission_sequence`, `recorded_at`, `action`, `confirmed_seats_delta`, `pending_seats_delta`, `reason` | One request; optionally references the triggering message |
| MissionProgress | `demand`, `confirmed`, `pending`, `unconfirmed`, `additional_needed`, `status` | Read-only view derived from one mission and its requests |
| RequestTiming | `submitted_at`, optional `response_received_at`, `waiting_seconds`, optional `response_elapsed_seconds` | Read-only time projection for one request at an observation instant |
| MobilisationPolicy | `policy_id`, `revision`, `name`, `selection_criteria` | Used by decisions and simulation runs |
| MobilisationDecision | `decision_id`, `recorded_at`, `remaining_demand` | One mission and policy revision; owns offer evaluations |
| OfferEvaluation | `evaluation_id`, `rank`, `proposed_seats`, `selected`, `reason` | One decision and one immutable offer revision |
| CommunicationMessage | `message_id`, `correlation_id`, `request_id`, `kind`, `payload`, `sent_at` | One request, including an unresolved ID for diagnostics; has one or more delivery records, including lost attempts |
| MessageDelivery | `delivery_id`, `attempt_number`, optional `received_at`, `disposition`, `reason`, optional `communication_rtt_seconds` | One logical message; duplicate deliveries retain the same message identity; received responses may report outbound-plus-return RTT, while lost attempts have no receipt or observed RTT |
| RunBaseline | `missions`, `market`, `command_index`, `message_index`, `delivery_index`, `decision_index` | Immutable starting snapshot; mission history and held quotes remain part of their owners |
| ScriptedResponse | `ship_id`, `request_ordinal`, `outcome`, optional `confirmed_seats` | One finite ship response rule addressed by request ordinal |
| RescueScenario | `scenario_id`, `revision`, `name`, `baseline`, `response_rules`, `availability_changes`, `time_horizon_seconds`, `seed`, `event_budget` | Owns communication profiles and baseline data; used by runs |
| CommunicationProfile | `profile_id`, `ship_id`, `outbound_delay_seconds`, `decision_delay_seconds`, `return_delay_seconds`, `loss_rule`, `duplication_rule`, `reordering_rule` | One scenario; applies to one baseline ship; rules are finite tuples of one-based request ordinals |
| SimulationRun | `run_id`, `scenario_id`, `scenario_revision`, `policy_id`, `policy_revision`, `started_at`, `finished_at`, `status`, optional `result` | One scenario and policy revision; owns an isolated run snapshot and result; does not mutate operational market state |
| SimulationResult | `completed`, `confirmed_seats`, `unmet_demand`, `requests_sent`, `released_seats`, optional `confirmation_elapsed_seconds`, optional `latest_arrival_estimate_seconds` | One completed or horizon-stopped run |
| RunSnapshot | `run`, `missions`, `market`, `command_index`, `message_index`, `delivery_index`, `decision_index` | Immutable business-state snapshot passed to result calculation |

## Keys, cardinalities and validation

- RunContext owns one central `(application_run_id, central_id)`, one market and zero or more missions keyed by mission_id. Registry and history reset in a fresh context. No relational database or persistence foreign keys are required.
- Mission owns zero or more requests and their applied history; demand is a positive integer fixed on registration. Station and ship names must be nonblank.
- Ship has zero or more immutable availability snapshots. Total seats may be zero to represent exhausted capacity; positive quantities are required for offers, RFQs and requests. available=False blocks new allocations regardless of total. Arrival duration is nonnegative. Snapshot identity and content cannot be reused inconsistently.
- A mission/ship pair has at most one ShipOffer; it has one or more immutable revisions numbered with positive integers. Highest revision_number wins, regardless of timestamp. A request's optional revision belongs to that mission and ship.
- One SeatRFQ targets one existing mission and ship and references one snapshot for that ship; it has zero or one RFQOffer. An offer is positive and no larger than requested_seats. It has one of held, accepted, rejected, expired. An accepted quote links to exactly one request; all other quotes link to none. RFQ statuses are pending, quoted, expired; quoted means a response exists, independent of that quote's lifecycle. Expire unanswered RFQs only at a supplied deadline.
- A SeatRequest belongs to one mission and ship, retains command_id, optionally links one originating quote, revision and decision. Originating references must agree on mission and ship. Full quote quantity transfers intact. Direct requests require an immutable offer-revision basis. Never overwrite that basis on later revisions.
- History has unique event_id and consecutive mission_sequence starting at 1. Exactly one entry per applied create or terminal transition. Ignored deliveries add no applied entries. Selection has one immutable policy revision and evaluations with unique rank and one revision basis each. A Candidate also carries `ship_id`, needed to apply the specified deterministic ship-ID tie-breakers when a revision value itself does not identify its ship.
- A CommunicationMessage carries one request ID, including unresolved references for unknown-request diagnostics. Its deliveries have distinct IDs and positive attempt numbers; loss has received_at=None and no observed RTT. A received response may report `communication_rtt_seconds`, distinct from response elapsed time. Payloads are finite typed immutable primitive values, not arbitrary executable objects.
- Scenario `(scenario_id, revision)` owns immutable baseline, finite ship/request-ordinal response rules and profiles, availability changes, positive finite horizon, nonnegative integer seed and positive finite `event_budget`. Reject unknown ship references, negative delays and unbounded event-generation rules. A response ordinal cannot be both lost and duplicated/reordered; a reordering rule gives its response lower priority than unmarked responses at the same instant. Runs reference exact scenario/policy revisions and own all mutable copies. A run has no result while running; a finalized run has exactly one result when completed or horizon_reached. `summarize` accepts a stopped pre-result `RunSnapshot`, and the runner publishes the finalized SimulationRun after calculating its result.

## Accounting and state transitions

For demand D: C=sum confirmed_seats; P=sum requested_seats of pending requests. `unconfirmed=D-C`, `additional_needed=D-C-P`. Enforce C>=0, P>=0, C+P<=D. Progress: complete iff C=D; awaiting_responses iff C<D and C+P=D; otherwise needs_more_help.

| Pending request operation | Terminal outcome | Confirmed delta | Pending delta |
| --- | --- | --- | --- |
| Full accept q | accepted | q=requested | -requested |
| Partial accept q | partially_accepted | 0<q<requested | -requested |
| Refuse | refused | 0 | -requested |
| Cancel | cancelled | 0 | -requested |
| Expire | expired | 0 | -requested |

Creation adds requested to pending and zero to confirmed. Terminal requests never transition again. Full/partial classifications must agree with quantity. Response timestamps cannot precede submission; closure is never earlier than submission. `mission.rules.timing(request: SeatRequest, now: Instant) -> RequestTiming` is read-only: before a response, response_elapsed is None and waiting is now-submitted_at; after a response, response_elapsed is response_received_at-submitted_at and waiting is zero. A response received at/after deadline first causes expiration, then gets a late disposition. No response_received_at is invented for cancellation/expiry.

Per ship: `used=held_unaccepted + pending + confirmed`; `free=max(0,total-used)`; `shortfall=max(0,used-total)`. New allocations require available, shortfall=0 and enough free capacity. Capacity reduction is the sole permitted external cause of used>total; it preserves settled data and blocks new allocations. Decreasing usage is always allowed. Requests also respect their immutable revision's capacity less other commitments against that logical offer; later revisions do not reset commitments.

Quote receipt reserves held quantity after rechecking latest inventory. Acceptance subtracts that same hold and adds pending atomically. Ship acceptance subtracts pending and adds confirmed; partial response releases the remainder. Quote rejection/expiry changes held only; request refusal/cancellation/expiry changes pending only. Never maintain independent mutable counters as a second authority: derive inventory from quotes and requests under one consistent snapshot.

## Atomicity and diagnostics

Application transaction reads consistent state, invokes Mission and market rules on staged values, validates both, appends applied history and successful-command result, then publishes once. Failure discards staged business state. A separately committed diagnostic delivery may explain failure without implying a business transition. Concurrent progress reads use the same store boundary. Identity normalization and response precedence are specified in [contracts](contracts/callable-api.md).

## Selection and experiment values

Earliest-arrival sorts `(revision.recorded_at + arrival_estimate_seconds, ship_id)`. Largest-capacity sorts `(-remaining_allocatable_capacity, arrival_instant, ship_id)`. Remaining capacity is constrained by latest market state and the revision; evaluate every candidate, record skipped reasons, propose no more than additional demand. Quote-backed proposals must match whole held quantities; skip an oversized hold rather than split it. Selection snapshots do not reserve inventory; acceptance revalidates atomically.

A SimulationResult uses C and D-C at stop; requests_sent counts creations, released_seats sums pending releases excluding quantities converted to confirmed. Completion time exists only when C=D. Latest arrival is the max revision/quote estimated arrival instant of confirmed requests minus run start, or None without confirmations. Communication RTT is outbound+return; response elapsed adds decision delay. These are distinct from arrival estimates.
