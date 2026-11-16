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
Model views: [domain model](../../docs/diagrams/rescue-domain-model/README.md),
[operations source](../../docs/diagrams/rescue-domain-model/class-diagrams/domain-model.mmd), and
[simulation source](../../docs/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd).
ER views: [operations ER source](../../docs/diagrams/rescue-domain-model/entity-relationship-diagrams/domain-model-er.mmd)
and [scenario ER source](../../docs/diagrams/rescue-domain-model/entity-relationship-diagrams/scenario-model-er.mmd).

## Clarifications

### Session 2026-11-16

- Q: Should we maintain both ER and UML class diagrams? → A: Both: ER for entities,
  attributes, and cardinalities; UML for class structure and, when agreed, behaviour,
  visibility, composition, and inheritance.
- Q: Should the rescue central be a separate orchestrator from a rescue mission? → A: Yes.
  RescueCentral receives and registers missions, coordinates mobilisation and request outcomes,
  handles cancellation and expiration, and provides progress. RescueMission remains separate and
  owns its requests, their state transitions, and mission invariants.
  RescueCentral coordinates mission operations and delegates request changes to the mission.
- Q: Which concept owns request state transitions and mission invariants? → A: RescueMission.
- Q: Should the central’s mission registry and mission history survive application restarts?
  → A: No. The registry, its missions, and their history live for one application run and reset
  when a new run starts. The central is used through callable API-style operations, with transport
  unspecified.

The [diagram index and legends](../../docs/diagrams/rescue-domain-model/README.md) link both
views of mission operations and scenario experiments. ER and UML views MUST preserve the same
data concepts, attributes, relationships, and cardinalities. UML also shows the agreed
RescueCentral application orchestrator, which has an identity scoped to one application run and is
represented in the operational ER view. It receives and registers missions, coordinates
mobilisation and request outcomes, handles cancellation and expiration, and provides progress. It
delegates request state changes to RescueMission, which owns requests, their state transitions, and
mission invariants.
Relationship roles describe domain participation; they do not introduce access-control roles.
Specific method signatures, visibility, and inheritance remain undecided until each concept is
reviewed. No superclass or permission model is implied by the access-control example.

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
8. **Given** an operator submits a mission to RescueCentral, **When** the mission is registered,
   **Then** the central can coordinate mobilisation, request responses, cancellation or expiration,
   and provide progress while the mission remains a separate concept.
9. **Given** a registered mission has a pending request, **When** RescueCentral coordinates a
   response, cancellation, or expiration, **Then** RescueMission validates and owns the resulting
   request transition and mission invariants, and the central provides the resulting progress.
10. **Given** a mission is registered during an application run, **When** the central is called
    again to coordinate it or provide progress, **Then** its registry entry, request state, and
    applied mission history remain available and consistent between calls.
11. **Given** an application run has ended, **When** a new run starts, **Then** its central has a
    new run-scoped identity and an empty mission registry and history.

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
3. **Given** a repeated command, **When** processed again, **Then** it creates no second request
   or applied transition; any recorded duplicate is distinguished from an applied change.
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
   from the same baseline with isolated mission, offers, requests, and history.
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
- **FR-008**: Preserve immutable offer revisions and link each request and selection decision to
  its revision basis. Current offer changes must not rewrite commitments. See Story 2.
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
- **FR-016**: Keep scenario execution isolated from operational missions and stop runs at their
  horizon even when messages remain pending. See Stories 4 and 5.
- **FR-017**: Provide a separate rescue central that receives and registers missions, coordinates
  mobilisation and request outcomes, delegates request changes to RescueMission, handles
  cancellation and expiration, and provides mission progress. RescueMission owns its requests,
  their state transitions, and mission invariants. See Story 1.
- **FR-018**: Keep the central's identity, mission registry, registered mission state, and
  associated mission history in memory for one application run. Callable API-style operations
  must preserve that state between calls; starting a new application run starts with an empty
  registry and history. See Story 1.

### Key Entities *(include if feature involves data)*

These are conceptual classes, not prescribed Python implementations. IDs identify data concepts;
linked objects need not duplicate relationship fields. Optional fields are explicitly marked.
RescueCentral is a run-scoped application entity: its `central_id` is unique within its
`application_run_id`. Its in-memory registry relates it to zero or more registered missions; the
existing mission request history remains available through those missions for the run.
Mission operations and scenario experiments are two views of this single feature: the latter
uses isolated copies of the former, rather than introducing a second set of rescue rules.

| Concept | Meaning and fields | Relationships |
| --- | --- | --- |
| RescueCentral | `central_id`, `application_run_id`; both identify the central within one run | Registers zero or more missions and retains their in-memory state and existing request history for that run; coordinates mobilisation and outcomes, delegating request changes to RescueMission |
| RescueMission | `mission_id`, `station_name`, `people_count`, `created_at` | Owns requests, their state transitions, mission invariants, and applied history; has calculated progress |
| Ship | `ship_id`, `name` | Has mission-specific offers; global fleet allocation is excluded |
| ShipOffer | `offer_id`, `mission_id`, `ship_id` | One logical offer per ship and mission; has one or more revisions |
| ShipOfferRevision | `revision_id`, `revision_number`, `capacity`, `arrival_estimate_seconds`, `available`, `recorded_at` | Immutable revision of one offer; referenced by requests and evaluations |
| SeatRequest | `request_id`, `command_id`, `requested_seats`, `confirmed_seats`, `outcome`, `submitted_at`, optional `response_received_at`, optional `response_deadline`, optional `closed_at` | One mission, one offer revision; optionally one originating decision |
| RequestHistoryEntry | `event_id`, `mission_sequence`, `recorded_at`, `action`, `confirmed_seats_delta`, `pending_seats_delta`, `reason` | One request; optionally references the triggering message |
| MissionProgress | `demand`, `confirmed`, `pending`, `unconfirmed`, `additional_needed`, `status` | Read-only view derived from one mission and its requests |
| MobilisationPolicy | `policy_id`, `revision`, `name`, `selection_criteria` | Used by decisions and simulation runs |
| MobilisationDecision | `decision_id`, `recorded_at`, `remaining_demand` | One mission and policy revision; owns offer evaluations |
| OfferEvaluation | `evaluation_id`, `rank`, `proposed_seats`, `selected`, `reason` | One decision and one immutable offer revision |
| CommunicationMessage | `message_id`, `correlation_id`, `kind`, `payload`, `sent_at` | One request; has one or more delivery records, including lost attempts |
| MessageDelivery | `delivery_id`, `attempt_number`, optional `received_at`, `disposition`, `reason` | One logical message; duplicate deliveries retain the same message identity |
| RescueScenario | `scenario_id`, `revision`, `name`, `baseline`, `response_rules`, `availability_changes`, `time_horizon_seconds`, `seed` | Owns communication profiles and baseline data; used by runs |
| CommunicationProfile | `profile_id`, `outbound_delay_seconds`, `decision_delay_seconds`, `return_delay_seconds`, `loss_rule`, `duplication_rule`, `reordering_rule` | One scenario; applies to one baseline ship |
| SimulationRun | `run_id`, `started_at`, `finished_at`, `status` | One scenario revision and policy revision; owns isolated mission state and result |
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

## Assumptions

- All six extensions are included by user choice. The detailed fields and rules below remain
  draft proposals for concept-by-concept review before implementation planning.
- A station is a mission attribute. A ship has a separate identity because offers change over time.
  Reservations are confirmed quantities on closed requests, not a separate entity.
- Ship offers are scoped to a mission. Capacity is the total offered to that mission, not an
  increment per revision; pending and confirmed requests across revisions consume that capacity.
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
  other ties use stable scenario event order. Message identity never changes across duplication.
- Communication RTT is the simulated outbound plus return transport delay. Response elapsed
  time includes ship decision delay. Real one-way network latency is not inferred from timestamps.
- Scenario responses are scripted by ship and request ordinal, with accepted quantities capped
  by the requested amount. Loss and duplication rules use fixed scripts or the recorded seed.
- Each comparison starts from the same versioned baseline and exogenous rules; policies may
  contact different ships, so their response sequences can differ in explainable ways.
- Confirmation elapsed time measures reservation completion. Latest arrival estimates describe
  the selected ships, not simulated evacuation completion. Incomplete runs have no completion time.
- Result arrival estimates use a common run-start reference: take the latest estimated arrival
  instant across confirmed ships and subtract the run start. With no confirmations the value
  is unknown. Released seats sums pending-seat releases from partial acceptance, refusal,
  cancellation, and expiration; it can exceed demand after repeated mobilisation.
- Simulation run states are `running`, `completed`, and `horizon_reached`. At the horizon,
  process events scheduled at that instant before stopping; deadline precedence still applies.
- No live market feed, trading integration, HTTP service, real timers, or fleet allocation across
  missions is required. Central operations are callable API-style operations; the transport is
  unspecified and no HTTP or web server is implied. Central identity, registry, registered mission
  state, and associated request history exist in memory for one application run and reset at the
  start of a new run. This does not add a separate audit log of every central command. Python class
  structure and concurrency mechanisms belong in the subsequent plan. Research analogies introduce
  no runtime dependency.
