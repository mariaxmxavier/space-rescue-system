# Feature Specification: Rescue Domain Model

**Feature Branch**: `main` (documentation draft; no feature branch created)

**Created**: 2026-11-16

**Feature Directory**: `specs/001-rescue-domain-model`

**Status**: Draft for concept-by-concept review

**Input**: Define the rescue domain's entities, fields, and relationships, with request history,
response timing, deadlines, versioned ship offers, decision explanations, scenario comparison,
and communication simulation.

Sources: [original problem](../../docs/context/original-problem.md) and
[constitution](../../.specify/memory/constitution.md).
Model views: [domain model](../../docs/architecture/diagrams/rescue-domain-model/README.md),
[operations source](../../docs/architecture/diagrams/rescue-domain-model/class-diagrams/domain-model.mmd), and
[simulation source](../../docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd).
ER views: [operations ER source](../../docs/architecture/diagrams/rescue-domain-model/entity-relationship-diagrams/domain-model-er.mmd)
and [scenario ER source](../../docs/architecture/diagrams/rescue-domain-model/entity-relationship-diagrams/scenario-model-er.mmd).

## Clarifications

### Session 2026-11-16

- Q: Should we maintain both ER and UML class diagrams? → A: Both: ER for entities,
  attributes, and cardinalities; UML for class structure and, when agreed, behaviour,
  visibility, composition, and inheritance.
- Q: Should the rescue central be a separate orchestrator from a rescue mission? → A: Yes.
  RescueCentral receives and registers missions, coordinates mobilisation and request outcomes,
  handles cancellation and expiration, and provides progress. Mission remains separate and
  owns its requests, their state transitions, and mission invariants.
  RescueCentral coordinates mission operations and delegates request changes to the mission.
- Q: Which concept owns request state transitions and mission invariants? → A: Mission.
- Q: Should the central’s mission registry and mission history survive application restarts?
  → A: No. The registry, its missions, and their history live for one application run and reset
  when a new run starts. The central is used through callable API-style operations, with transport
  unspecified.
- Q: What identifies a RescueCentral within an application run? → A: The composite identity
  `(application_run_id, central_id)`. This identifies the central; mission multiplicity is
  expressed separately by the registry association.
- Q: How many RescueCentral instances exist per application run, and how does the central
  identify a registered mission? → A: Exactly one RescueCentral exists per application run and
  registers multiple Mission instances. Each Mission is identified by its `mission_id`; the
  central looks up missions in its registry by that ID. Do not add one mission_id to RescueCentral
  or prescribe a persistence foreign key.
- Q: Which identifier does RescueCentral use to identify an existing mission? → A: The Mission
  primary key, `mission_id`. This settles the identity used to look up an existing mission; it
  does not prescribe what other data an operation may carry. Registering a mission still requires
  mission data.
- Q: Can a registered mission's `people_count` change? → A: No. The count is fixed when the
  mission is registered; any later attempt to change it is rejected. This is a domain invariant,
  independent of UML visibility.
- Q: Should `command_id` remain on `SeatRequest` so a repeated request-creation command can be
  recognized? → A: Yes. Keep `command_id` on `SeatRequest` for recognizing repeated request-creation
  commands. This does not settle the command's scope, payload comparison, collision handling, or
  persistence mechanism.
- Q: Which offer revision is current for a ship offer? → A: The revision with the highest
  `revision_number` is current. Earlier revisions remain immutable history; `recorded_at` does not
  determine revision order.
- Q: How should changing ship availability be coordinated across missions? → A: Use a
  `B3Market` to coordinate time-specific requests for quotation (RFQs), sending one RFQ to each ship available for the mission at that time. Each RFQ addresses one ship and receives at most one RFQOffer response. Each
  responding RFQ offer temporarily holds its offered seats until central acceptance, quote
  rejection, or explicit expiry. An offer is not confirmed transport; central acceptance transfers
  its hold into a pending `SeatRequest` for ship confirmation. Only the ship's acceptance of that
  request confirms seats. B3Market counts active unaccepted holds, pending requests, and confirmed
  commitments across missions against availability, counting each quantity once. Quote rejection or
  expiry releases only an unaccepted hold. This adds inventory safety to
  the original scope; fleet-wide optimisation remains excluded. Expiry duration and policy are
  unspecified.
- Q: Should the ship and offer concepts be grouped with B3Market in the conceptual model? → A: Yes. Use a distinct `ShipMarket` namespace for `B3Market`, `Ship`, `ShipAvailability`, `SeatRFQ`, `RFQOffer`, `ShipOffer`, and `ShipOfferRevision`; keep `Mission` and `SeatRequest` in `MissionOperations`. The namespace is an organizational grouping in the model, not a code package or service boundary. Relationships across groups remain explicit. Simulation runs retain isolated market copies and do not mutate operational market state.

The [diagram index and legends](../../docs/architecture/diagrams/rescue-domain-model/README.md) link both
views of mission operations and scenario experiments. ER and UML views MUST preserve the same
data concepts, attributes, relationships, and cardinalities. UML also shows the agreed
exactly one RescueCentral application orchestrator per application run, whose identity is
represented in the operational ER view. Its registry is keyed by Mission `mission_id`; this is a
conceptual lookup relationship, not a prescribed storage mechanism. It receives and registers
missions, coordinates mobilisation and request outcomes, handles cancellation and expiration, and
provides progress. It
delegates request state changes to Mission, which owns requests, their state transitions, and
mission invariants.
Relationship roles describe domain participation; they do not introduce access-control roles.
All UML attributes, including Mission's four data attributes, are marked private as a proposed
encapsulation convention, not an approved visibility decision. The Mission attributes are:
`mission_id`, `station_name`, `people_count`, and `created_at`. This proposal may protect mission state so that operations can preserve request-transition and
mission invariants; it does not make the values immutable. No public Mission operations, accessors,
or mutators are specified. RescueCentral's existing agreed callable responsibilities are shown with proposed public visibility,
but their exact signatures remain open. No
operations are invented for other classes. `people_count` is fixed after registration as a separate
domain invariant; private visibility does not establish that rule. The ER views retain the same data attributes without
visibility because ER notation describes data and relationships, not member access. No superclass
or permission model is implied by the access-control example. Both UML diagrams render all three class compartments: class name, attributes, and operations.
For classes without specified operations, Mermaid renders the operations compartment empty; no
placeholder members are needed.

The UML views group related concepts in named namespaces for conceptual organization only.
`MissionOperations` contains `Mission` and `SeatRequest`; `ShipMarket` contains `B3Market`,
`Ship`, `ShipAvailability`, `SeatRFQ`, `RFQOffer`, `ShipOffer`, and `ShipOfferRevision`.
Cross-namespace relationships remain part of the model: missions request quotations and own
seat requests, requests may retain an RFQ offer and an offer-revision basis, and B3Market sends
RFQs. These groups do not prescribe code packages, deployment units, or service boundaries.
Simulation references/copies keep the same conceptual grouping while each run owns isolated
market availability and holds; operational market state is unchanged.

Rendering MUST use ELK hierarchical layout with orthogonal connections, consistent spacing,
and visual grouping. Rendered views MUST be inspected for overlapping nodes, labels, and
edges. Visual optimisation MUST NOT change domain semantics.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Coordinate seats safely (Priority: P1)

An operator submits a mission to RescueCentral, which registers it, coordinates ship offers,
seat requests and outcomes, and provides progress showing whether to seek more help, await
responses, or declare transport guaranteed.

**Why this priority**: All extras depend on correct rescue accounting.

**Independent Test**: Coordinate a ten-person mission using explicit requests and responses,
without automatic selection or communication simulation.

**Acceptance Scenarios**:

1. **Given** demand 10 and a pending request for 6 seats, **When** 4 seats are accepted,
   **Then** the request closes, 4 seats are confirmed, none remain pending, and 6 are needed.
2. **Given** 4 confirmed and 6 pending seats, **When** another seat is requested,
   **Then** the operation is rejected without changing recorded commitments.
3. **Given** 10 confirmed seats, **When** progress is consulted, **Then** the mission is complete;
   10 pending seats alone never produce that result.
4. **Given** a pending request for 6 seats, **When** it is fully accepted,
   **Then** 6 seats become confirmed and none remain pending.
5. **Given** a pending request for 6 seats, **When** it is refused, cancelled, or expired,
   **Then** zero seats become confirmed and all 6 pending seats are released.
6. **Given** closed requests or simultaneous competing operations, **When** messages repeat,
   arrive late, or arrive out of order, **Then** closed decisions remain final and seat limits hold.
7. **Given** only 3 allocatable seats on a ship and unmet mission demand of 10,
   **When** 4 seats are requested from that ship, **Then** the request is rejected without mutation.
8. **Given** an application run starts, **When** its central is initialized and multiple missions
   are registered, **Then** exactly one RescueCentral serves the run and each mission remains
   independently identifiable by `mission_id` and retrievable without conflating mission state.
9. **Given** an operator submits a mission to RescueCentral, **When** the mission is registered,
   **Then** the central can coordinate mobilisation, request responses, cancellation or expiration,
   and provide progress while the mission remains a separate concept.
10. **Given** a registered mission has a pending request, **When** RescueCentral coordinates a
   response, cancellation, or expiration, **Then** Mission validates and owns the resulting
   request transition and mission invariants, and the central provides the resulting progress.
11. **Given** a mission is registered during an application run, **When** the central is called
    again to coordinate it or provide progress, **Then** its registry entry, request state, and
    applied mission history remain available and consistent between calls.
12. **Given** an application run has ended, **When** a new run starts, **Then** its central has a
    new run-scoped identity and an empty mission registry and history.
13. **Given** a mission is already registered, **When** RescueCentral performs an operation on
    that mission, **Then** it identifies the mission by its `mission_id` primary key.
14. **Given** a mission has been registered with a people count, **When** an operation attempts to
    change that count, **Then** the change is rejected and the registered count remains unchanged.
15. **Given** a ship offer has multiple immutable revisions, **When** its current revision is
    determined, **Then** the revision with the highest `revision_number` is current, regardless
    of `recorded_at`, and earlier revisions remain available as history.
16. **Given** multiple missions seek seats from the same ship, **When** B3Market receives a
    time-specific RFQ offer, **Then** it holds offered seats against ship availability until central
    acceptance, quote rejection, or explicit expiry, and prevents overbooking across missions.
17. **Given** an RFQ offer has been returned but not accepted, **When** mission progress is
    consulted, **Then** its held seats are not confirmed transport and cannot complete the mission.
18. **Given** an unaccepted RFQ offer is rejected or expires, **When** B3Market updates availability,
    **Then** its hold is released; central acceptance transfers the hold into a pending SeatRequest
    and does not itself confirm seats.
19. **Given** the operational and scenario conceptual views are organized into namespaces, **When**
    their group membership is inspected, **Then** `ShipMarket` groups B3Market, Ship, ShipAvailability,
    SeatRFQ, RFQOffer, ShipOffer, and ShipOfferRevision, while Mission and SeatRequest remain in
    MissionOperations; cross-group relationships are retained and the grouping implies no package
    or service boundary. Each simulation run still owns isolated market state and leaves operational
    market data unchanged.

### User Story 2 - Explain decisions and changing offers (Priority: P2)

An operator inspects request history and the information behind selection or rejection,
including the offer revision known at the time.

**Why this priority**: Current availability alone cannot explain past commitments.

**Independent Test**: Change an offer after a request and inspect its preserved basis and history.

**Acceptance Scenarios**:

1. **Given** an offer of 30 seats, **When** a request is created and a later revision offers 10,
   **Then** the request still references the original revision and keeps its original quantity.
2. **Given** a selection decision, **When** its explanation is inspected, **Then** the policy,
   considered offer revisions, selected and skipped ships, and reasons are visible.
3. **Given** a request-creation command has already created a `SeatRequest`, **When** that same
   command is retried, **Then** no duplicate request is created. The request retains its
   `command_id` so the repeated command can be recognized. This acceptance does not define command
   scope, payload comparison, collision handling, or persistence.
4. **Given** a revision reducing capacity below existing commitments, **When** published,
   **Then** commitments remain unchanged, the shortfall is visible, and new requests are blocked
   until capacity permits them.

### User Story 3 - Understand waiting and deadlines (Priority: P2)

An operator sees response elapsed time and expires unanswered requests at a defined deadline.

**Why this priority**: Slow responses tie up demand even when a ship can arrive quickly.

**Independent Test**: Advance a controlled timeline through submission, response, and expiration.

**Acceptance Scenarios**:

1. **Given** submission at second 10 and decision receipt at second 17, **When** timing is shown,
   **Then** response elapsed time is 7 seconds, separately from physical arrival estimates.
2. **Given** a deadline at second 20, **When** expiration is processed at second 20 before a
   response, **Then** pending seats are released and a subsequent response cannot reopen it.
3. **Given** a response and expiration at the same simulated instant, **When** processed,
   **Then** expiration wins deterministically and the response is recorded as late.
4. **Given** no received response, **When** timing is shown, **Then** elapsed waiting is reported
   and response elapsed time remains unknown rather than zero.

### User Story 4 - Compare what-if outcomes (Priority: P3)

An operator runs multiple mobilisation policies against the same scenario and compares results
without changing the operational mission.

**Why this priority**: It makes policy choices explainable using reproducible evidence.

**Independent Test**: Compare earliest-arrival and largest-capacity policies over a fixed scenario.

**Acceptance Scenarios**:

1. **Given** a saved baseline and response rules, **When** each policy runs, **Then** each starts
   from the same baseline with isolated mission, B3Market availability and holds, offers, requests,
   and history.
2. **Given** refusals, capacity changes, and delayed responses, **When** runs finish,
   **Then** results report completion, confirmed and unmet demand, request count, released seats,
   simulated time to confirmation, and latest arrival estimate among confirmed ships.
3. **Given** the same scenario revision, policy revision, and seed, **When** rerun,
   **Then** decisions and business results are identical.
4. **Given** an incomplete run, **When** results are compared, **Then** it is marked incomplete
   and has no fabricated completion time or successful-completion ranking.

### User Story 5 - Exercise unreliable communication (Priority: P3)

An operator configures communication delays, decision delays, loss, duplication, and reordered
delivery to observe how rescue commitments survive communication failures.

**Why this priority**: Communication failures must be visible without weakening accounting.

**Independent Test**: Deliver a scripted response twice, lose another, and delay a third past expiry.

**Acceptance Scenarios**:

1. **Given** outbound delay 2 seconds, decision delay 5, and return delay 3,
   **When** a response arrives, **Then** communication RTT is 5 seconds and response elapsed
   time is 10 seconds in this simulation; ship arrival remains a separate estimate.
2. **Given** duplicated or reordered deliveries, **When** processed, **Then** their shared logical
   identity prevents repeated effects and history explains ignored deliveries.
3. **Given** a lost response and a response deadline, **When** the run reaches the deadline,
   **Then** the request expires and later mobilisation can use the released demand.
4. **Given** a scenario with no reachable completion, **When** its time horizon is reached,
   **Then** the run stops and reports incomplete demand and outstanding requests.

### Edge Cases

- Reject empty identities, non-positive demand, capacity, or requested quantities, fractional
  quantities, booleans as quantities, negative or non-finite durations, and confirmations larger
  than the request. Zero confirmed seats is valid for refusal, cancellation, and expiration.
- Retain stable logical identities across retries; reject reuse of an identity with changed content.
- Unknown requests and conflicting responses cannot mutate a mission; record their disposition.
- A partial acceptance is final, even if another response offers the remainder later.
- Cancellation before delivery does not imply the remote message disappeared.
- Offer revisions must not create fresh capacity by resetting earlier reservations.
- Equal arrival or capacity values use a stable ship-ID tie-breaker; unavailable ships are skipped.
- Zero communication delay is valid; missing observations are unknown, not zero.
- Rejected operations cannot add applied business-history entries or change commitments.
- Multiple ships or repeated requests must not double-count capacity for the same ship and mission.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Register identifiable missions, ships, and mission-specific ship offers with valid
  seat quantities and arrival estimates. See Story 1 and input edge cases.
- **FR-002**: Preserve non-negative confirmed and pending totals and `confirmed + pending <= demand`.
  New requests must respect both remaining mission demand and ship capacity. See Story 1.
- **FR-003**: Support full acceptance, partial acceptance, refusal, cancellation, and expiration.
  Only pending requests can transition; a partial response releases the remainder. See Story 1.
- **FR-004**: Derive mission progress from request outcomes and declare completion only when
  confirmed seats equal demand. See Story 1.
- **FR-005**: Preserve accepted state under invalid, duplicate, conflicting, late, unknown, or
  reordered messages and competing operations. See Stories 1, 2, and 5.
- **FR-006**: Keep append-only applied request history with a stable event identity, mission
  sequence, recorded time, action, quantities, and reason. See Story 2.
- **FR-007**: Record message dispositions separately from applied transitions, correlating
  submissions, responses, duplicates, and rejection reasons. See Stories 2 and 5.
- **FR-008**: Preserve immutable mission-specific ShipOffer revisions and link each request and selection decision to
  its revision basis. Current offer changes must not rewrite commitments. An RFQOffer is a separate time-specific quote linked to its SeatRFQ; accepting it creates the request and records its originating quote and any ShipOffer revision basis used. See Story 2.
- **FR-009**: Explain each selection using its policy revision, considered offer revisions,
  proposed quantities, and selected or skipped reasons. See Story 2.
- **FR-010**: Expose submission, response receipt, waiting duration, and response elapsed time.
  Keep communication RTT, ship decision delay, and physical arrival estimates distinct.
  See Stories 3 and 5.
- **FR-011**: Support optional response deadlines and explicit expiration; a response received at
  or after the deadline cannot confirm seats. Expire before applying it. See Story 3.
- **FR-012**: Save versioned scenario baselines with ship response rules, availability changes,
  communication profiles, a time horizon, and reproducibility seed. See Stories 4 and 5.
- **FR-013**: Compare earliest-arrival and largest-capacity policies using the same scenario
  revision and initial state, with independent run state and stable tie-breaking. See Story 4.
- **FR-014**: Simulate outbound delay, ship decision delay, return delay, message loss, duplicate
  deliveries, and reordering using a controlled timeline. See Story 5.
- **FR-015**: Report each run's completion, confirmed and unmet demand, request count, released
  seats, confirmation time if completed, and latest confirmed ship arrival estimate. See Story 4.
- **FR-016**: Keep scenario execution isolated from operational missions and B3Market state, with
  independent mission, availability, and hold copies; stop runs at their horizon even when messages
  remain pending. See Stories 4 and 5.
- **FR-017**: Provide a separate rescue central that receives and registers missions, coordinates
  mobilisation and request outcomes, delegates request changes to Mission, handles
  cancellation and expiration, and provides mission progress. Mission owns its requests,
  their state transitions, and mission invariants. See Story 1.
- **FR-018**: Keep the central's identity, mission registry, registered mission state, and
  associated mission history in memory for one application run. Callable API-style operations
  must preserve that state between calls; starting a new application run starts with an empty
  registry and history. See Story 1.
- **FR-019**: Require exactly one RescueCentral per application run, registering multiple Mission
  instances in a registry addressable by each mission's `mission_id`. Each mission remains
  independently identifiable and owns its own requests and mission invariants. This requirement
  does not prescribe concurrent mission execution or registry storage. See Story 1.
- **FR-020**: Keep a registered mission's people count fixed for its lifetime; reject attempts to
  change it after registration. See Story 1.
- **FR-021**: Retain `command_id` on each `SeatRequest` so a repeated request-creation command can
  be recognized and cannot create a duplicate request. Command scope, payload comparison,
  collision handling, and persistence remain unspecified. See Story 2.
- **FR-022**: Determine the current revision of each ship offer by the highest `revision_number`;
  preserve earlier revisions as immutable history and do not use `recorded_at` to order revisions.
  See Story 2.
- **FR-023**: Use B3Market to track changing ship availability and coordinate time-specific RFQs
  across missions. Send one SeatRFQ to each ship available for the mission when issued; each RFQ targets one ship, references its ShipAvailability snapshot, and receives at most one RFQOffer. A responding offer temporarily holds its offered seats and does not count as confirmed
  transport. Central acceptance transfers the full held quantity atomically into a pending SeatRequest for ship confirmation;
  quote rejection or explicit expiry releases only an unaccepted hold. Expiry duration and policy remain unspecified. See Story 1.
- **FR-024**: Account for all active holds and SeatRequest commitments across missions against each
  ship's latest ShipAvailability total to prevent overbooking. For each ship, active unaccepted RFQOffer holds plus pending SeatRequest seats plus confirmed SeatRequest seats MUST not exceed latest `total_seats`. Count each quantity once: acceptance atomically transfers the hold into pending seats; ship acceptance transfers pending to confirmed; refusal, cancellation, or expiry releases unconfirmed pending seats. Capacity reductions expose a shortfall and block new allocations without erasing commitments.
  This inventory-safety extension does not require fleet-wide optimisation. See Story 1.
- **FR-025**: Organize the conceptual model into `MissionOperations` (`Mission`, `SeatRequest`,
  and mission operation concepts) and `ShipMarket` (`B3Market`, `Ship`, `ShipAvailability`,
  `SeatRFQ`, `RFQOffer`, `ShipOffer`, and `ShipOfferRevision`). Preserve modeled relationships
  across the groups. These namespaces are conceptual organization and do not prescribe code or
  deployment boundaries. Scenario runs retain isolated copies of market state and do not mutate
  the operational market. See Story 4.

### Key Entities *(include if feature involves data)*

These are conceptual classes, not prescribed Python implementations. IDs identify data concepts;
linked objects need not duplicate relationship fields. Optional fields are explicitly marked.
Exactly one RescueCentral exists per application run, identified by the composite key
(`application_run_id`, `central_id`). It holds a conceptual registry of zero or more Mission
instances keyed by each Mission's `mission_id`; this does not prescribe a foreign key or storage
format. Registered mission state and existing request history remain available through those
missions for the run.
Mission operations and scenario experiments are two views of this single feature: the latter
uses isolated copies of the former, rather than introducing a second set of rescue rules. The
conceptual namespace grouping is shared across views; simulation copies remain run-local and
operational market state is not mutated.

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
| MobilisationPolicy | `policy_id`, `revision`, `name`, `selection_criteria` | Used by decisions and simulation runs |
| MobilisationDecision | `decision_id`, `recorded_at`, `remaining_demand` | One mission and policy revision; owns offer evaluations |
| OfferEvaluation | `evaluation_id`, `rank`, `proposed_seats`, `selected`, `reason` | One decision and one immutable offer revision |
| CommunicationMessage | `message_id`, `correlation_id`, `kind`, `payload`, `sent_at` | One request; has one or more delivery records, including lost attempts |
| MessageDelivery | `delivery_id`, `attempt_number`, optional `received_at`, `disposition`, `reason`, optional `communication_rtt_seconds` | One logical message; duplicate deliveries retain the same message identity; a received response may report outbound-plus-return RTT |
| RescueScenario | `scenario_id`, `revision`, `name`, `baseline`, `response_rules`, `availability_changes`, `time_horizon_seconds`, `seed` | Owns communication profiles and baseline data; used by runs |
| CommunicationProfile | `profile_id`, `outbound_delay_seconds`, `decision_delay_seconds`, `return_delay_seconds`, `loss_rule`, `duplication_rule`, `reordering_rule` | One scenario; applies to one baseline ship |
| SimulationRun | `run_id`, `started_at`, `finished_at`, `status` | One scenario revision and policy revision; owns isolated mission and B3Market availability/hold state and result; does not mutate operational market state |
| SimulationResult | `completed`, `confirmed_seats`, `unmet_demand`, `requests_sent`, `released_seats`, optional `confirmation_elapsed_seconds`, optional `latest_arrival_estimate_seconds` | One completed or horizon-stopped run |

Request outcomes are `pending`, `accepted`, `partially_accepted`, `refused`, `cancelled`, and
`expired`. All except `pending` are terminal. Mission progress is `complete` when confirmed
equals demand, `awaiting_responses` when confirmed plus pending equals demand but confirmation
is incomplete, and `needs_more_help` otherwise.

Full acceptance confirms exactly the requested quantity. Partial acceptance confirms a positive
integer smaller than that quantity. Refusal confirms zero. Cancellation and expiration confirm
zero and cannot apply after any response has closed the request.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every acceptance scenario preserves seat limits and closed outcomes; no invalid
  operation changes accepted commitments.
- **SC-002**: Every created request and applied outcome has exactly one corresponding applied
  history entry; every automated selection identifies its policy and offer-revision basis.
- **SC-003**: The same scenario, policy revision, and seed produce identical business histories
  and results over three runs, excluding run IDs and wall-clock metadata.
- **SC-004**: Two policies can be compared across at least three scenarios: ordinary responses,
  partial acceptance with refusal, and delayed or lost messages with changing availability.
- **SC-005**: The 2 + 5 + 3 second communication example reports a 10-second response elapsed
  time and 5-second communication RTT; responses at or after expiration confirm zero new seats.
- **SC-006**: Running all comparison scenarios leaves the operational mission and history unchanged.
- **SC-007**: Across repeated callable operations within one application run, registered missions and
  their applied request history remain available and consistent; after a new run starts, the
  central registry and history are empty.
- **SC-008**: Both conceptual views use the agreed `ShipMarket` membership and preserve all
  cross-namespace associations; every simulation run uses isolated market state, leaving the
  operational market unchanged. No namespace is interpreted as a required code or service boundary.

## Assumptions

- All six extensions are included by user choice. The detailed fields and rules below remain
  draft proposals for concept-by-concept review before implementation planning.
- A station is a mission attribute. A ship has a separate identity because offers change over time.
  Reservations are confirmed quantities on closed requests, not a separate entity.
- B3Market coordinates changing availability and RFQs across missions. Active unaccepted RFQOffer holds, pending SeatRequest commitments, and confirmed SeatRequest
  commitments consume ship availability, each quantity counted once. Central acceptance atomically
  transfers a quote hold into a pending SeatRequest; only ship acceptance confirms seats. Quote
  rejection or expiry releases only an unaccepted hold, while ship refusal releases the pending
  request commitment. This prevents overbooking
  without introducing fleet-wide optimisation. For conceptual organization, `Ship`,
  `ShipAvailability`, `SeatRFQ`, `RFQOffer`, `ShipOffer`, and `ShipOfferRevision` are grouped with
  `B3Market` under `ShipMarket`; the offer concepts retain their existing mission-specific offer-history
  meaning and the highest revision number remains current. This grouping does not imply a code or
  service boundary.
- Capacity reductions do not revoke confirmations or rewrite pending requests. They flag a
  shortfall and block new allocations; an operator may cancel pending requests to resolve it.
- Arrival estimates are non-negative durations in seconds relative to the observation time of
  the offer revision. They are not deadlines or travel simulations. Compare absolute estimated
  arrival instants when revisions have different observation times.
- Earliest-arrival selects by estimated arrival instant, then ship ID. Largest-capacity selects
  by remaining allocatable capacity descending, then arrival instant, then ship ID.
- Applied history explains state changes; delivery records explain ignored messages. This does
  not require event sourcing or reconstructing state from history.
- All simulated timing shares one timeline. Equal-time expiration precedes response delivery;
  other ties use stable scenario event order. A response ordinal named by `reordering_rule` is
  processed after unmarked response deliveries at the same instant. A response ordinal cannot be
  both lost and duplicated or reordered. Message identity never changes across duplication.
- Communication RTT is the simulated outbound plus return transport delay. Response elapsed
  time includes ship decision delay. Real one-way network latency is not inferred from timestamps.
- Scenario responses are scripted by ship and request ordinal, with accepted quantities capped
  by the requested amount. Loss and duplication rules use fixed scripts or the recorded seed.
- Each comparison starts from the same versioned baseline and exogenous rules, including an
  isolated B3Market availability/hold state; operational mission and market state are not mutated.
  Policies may contact different ships, so their response sequences can differ in explainable ways.
- Confirmation elapsed time measures reservation completion. Latest arrival estimates describe
  the selected ships, not simulated evacuation completion. Incomplete runs have no completion time.
- Result arrival estimates use a common run-start reference: take the latest estimated arrival
  instant across confirmed ships and subtract the run start. With no confirmations the value
  is unknown. Released seats sums pending-seat releases from partial acceptance, refusal,
  cancellation, and expiration; it can exceed demand after repeated mobilisation.
- Simulation run states are `running`, `completed`, and `horizon_reached`. At the horizon,
  process events scheduled at that instant before stopping; deadline precedence still applies.
- No live external market feed, trading integration, HTTP service, or real timers are required.
  Inventory safety across missions is required; fleet-wide optimisation remains excluded. Exactly one central exists per run, and its registry is keyed by Mission
  `mission_id`; this does not prescribe a storage foreign key. Central operations are callable API-style operations; the transport is
  unspecified and no HTTP or web server is implied. Central identity, registry, registered mission
  state, and associated request history exist in memory for one application run and reset at the
  start of a new run. This does not add a separate audit log of every central command. Python class
  structure and concurrency mechanisms belong in the subsequent plan. Research analogies introduce
  no runtime dependency.
