# Feature Specification: Clear and Ordered Communication

**Feature Branch**: `007-communication-conformance`

**Created**: 2026-11-16 | **Updated**: 2026-11-17

**Status**: Draft, ready for planning

**Input**: Simplify all of spec 007; split communication classes and rules into nested files; explain what, when and why; link UML and ER; use the ordering and recovery approach closest to B3 Binary EntryPoint guidelines. Revised 2026-11-17: introduce the decision-ordering algorithm closest to B3's matching engine (per-segment FIFO sequencing with price/time priority), after researching current market solutions.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Process responses safely (Priority: P1)

As a rescue operator, I need repeated, conflicting, lost and late responses to have clear outcomes without counting seats twice or changing a closed decision.

**Why this priority**: Communication must protect rescue commitments.

**Independent Test**: Exercise each delivery case and check its decision, reason and resulting seat totals.

**Acceptance Scenarios**:

1. **Given** an identical recorded delivery, **When** it arrives again, **Then** it is ignored without adding history or changing seats.
2. **Given** an existing message or delivery identity, **When** different content reuses it, **Then** an identity conflict is reported and the accepted content remains unchanged.
3. **Given** a lost attempt, **When** the same message arrives through a new delivery identity, **Then** it can affect the request at most once.
4. **Given** an unknown request, an invalid time, a closed request or an expired deadline, **When** a response arrives, **Then** the existing rejection, loss, ignore or late policy applies and closed decisions stay final.

### User Story 2 - Sequence and recover messages (Priority: P1)

As an operator, I need missed and repeated messages identified within each ship session, and missing central reports recoverable without applying a response twice.

**Why this priority**: A missing message must be visible without stopping unrelated valid responses or changing settled seats.

**Independent Test**: Simulate a gap in each direction, recover missing reports, retry a response, and inspect session counters and mission totals.

**Acceptance Scenarios**:

1. **Given** a new ship session version, **When** business messages start, **Then** each direction starts at sequence 1 and maintains its own counter.
2. **Given** the central expects inbound 2, **When** inbound 3 arrives, **Then** it records a NotApplied notification for 2, considers 3 under the normal business rules, and next expects 4 without waiting for 2.
3. **Given** a missing response, **When** the ship resubmits it with a new sequence and delivery identity, **Then** the message can affect seats at most once; a delayed message below the expected sequence cannot apply it again.
4. **Given** a ship receives central report 3 while expecting 2, **When** it requests recovery, **Then** original reports are replayed in sequence order with their original identities and numbers, without rerunning mission transitions.
5. **Given** a session resumes or a run copies its baseline, **When** messaging continues, **Then** counters and recoverable reports continue without reuse or mutation of the source run; a stale session version cannot change the active session.
6. **Given** a control message, exact delivery retry or failed transaction, **When** it is handled, **Then** no extra business sequence is consumed by the control/retry, and no receiver state is partially committed on failure.
7. **Given** simultaneous messages from different ship sessions, **When** they compete for shared seats, **Then** atomic mission updates preserve capacity even though their session sequence numbers are incomparable.
8. **Given** a recovery request outside retained active-version history, over 1000 reports, or overlapping an outstanding request, **When** it is checked, **Then** it is rejected explicitly without business effects or fabricated reports.

### User Story 3 - Order competing decisions per mission (Priority: P1)

As an operator, I need simultaneous responses, cancellations and expiries for one mission to take effect in one clear, repeatable order, so that I can see which action won and replay the mission's history in that order.

**Why this priority**: Several operators and ships act at the same time. Without one authoritative order per mission, two observers can disagree on which decision came first.

**Independent Test**: Submit competing actions for one mission and independent actions for another mission, then check the mission order numbers, the winner of each race and the seat totals.

**Acceptance Scenarios**:

1. **Given** a mission with no decisions yet, **When** its first decision commits, **Then** it receives mission order 1, and each later committed decision for that mission receives the next number, without gaps or reuse.
2. **Given** two responses for the same mission arriving at central one after the other, **When** they are processed, **Then** they take effect in central arrival order, whatever their sender times or session numbers say.
3. **Given** an operator cancellation and a ship confirmation racing for the same request, **When** both reach central, **Then** whichever central registers first decides the request; the other gets the closed-request outcome, and its report names the mission order number it was evaluated after.
4. **Given** decisions for two different missions, **When** they arrive at the same time, **Then** each mission keeps its own order, and neither waits for nor numbers the other.
5. **Given** a retried message, **When** it arrives through a new delivery, **Then** it takes a new place at the back of the mission queue, keeping its message identity; it never takes back the original attempt's place.
6. **Given** a failed transaction, a report replay, or a duplicate that has no business effect, **When** it is handled, **Then** it consumes no mission order number.
7. **Given** decision reports from several ship sessions for one mission, **When** an observer collects them, **Then** each report carries its mission order number, so the observer can rebuild the mission's history in order and detect a missing decision.

### User Story 4 - Understand and maintain communication (Priority: P2)

As a maintainer, I need small, named parts and explanations that agree with the UML and ER, so I can find a rule and understand why it exists.

**Why this priority**: Safe changes depend on making responsibilities and relationships visible.

**Independent Test**: Trace a response from the application to its communication rule, model, explanation and diagrams.

**Acceptance Scenarios**:

1. **Given** any communication class or public rule, **When** a maintainer opens it, **Then** its purpose, caller, timing, rationale and diagram links are documented.
2. **Given** the communication package, **When** its structure is checked, **Then** each class or public rule has its own file in a meaningful nested folder.
3. **Given** the delivery rules, **When** they are tested directly, **Then** they need no storage, network, real clock or application wiring.

### Edge Cases

- A reused delivery identity conflicts even when its message identity is unchanged.
- A received response for an unknown request is ignored; an attempt with no receipt is recorded as lost, following current precedence.
- Receipt before send is invalid; send before request submission is invalid; receipt exactly at the deadline is late.
- A new attempt for an already applied message is recorded without applying seats again.
- A conflicting message with a new delivery identity may record a rejection, but never replaces the original message.
- A lost inbound send consumes its sender number, but cannot advance the central's expected number until a message or synchronisation control is received.
- A skipped inbound message cannot later execute under its old sequence; recovery uses a new sequence and delivery identity with the same immutable message identity.
- Session control messages, including NotApplied, do not consume business sequence numbers. Replay does not allocate new numbers.
- Advancing an inbound expectation with Sequence reports the skipped range; rewinding is rejected. Recovery completion identifies the next live-stream sequence.
- A received, well-formed business message consumes its sequence even when business rules reject it; a transaction failure does not commit receiver progress.
- Sequence numbers are comparable only within a session version and direction. Timestamps do not reorder committed decisions.
- Mission order numbers are comparable only within one mission. They give the order of committed decisions, not the order ships sent them.
- Only a decision that appends to the mission history consumes a mission order number: a request creation, an accepted, partial or refused response, a cancellation or an expiry. A rejected, ignored or late response consumes none; its report names the last mission order number it was evaluated after.
- Two responses with equal sender times are ordered by central arrival. Rescue responses carry no price, so arrival order is the whole priority rule.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Delivery classification MUST be independent of storage and application orchestration; the application MUST apply its decision without duplicating communication rules. Verified by Story 4.
- **FR-002**: Delivery outcomes and reasons MUST use a closed, named vocabulary, including applied, ignored, lost, rejected and late outcomes. Verified by Story 1's decision cases.
- **FR-003**: Existing duplicate, identity-conflict, time, loss, unknown-request, deadline and final-outcome policies MUST remain valid. Verified by Story 1 and the edge cases.
- **FR-004**: Business messages MUST carry a ship-session identity, session version, direction and positive sequence number. Each direction MUST have separate sequence state, starting at 1 for a new version. Sender allocation occurs on sending, not on receipt. Verified by Story 2.1 and lost-send cases.
- **FR-005**: Ship-to-central responses MUST use idempotent sequencing: below-expected messages cannot execute again; a higher-than-expected message MUST report the missing range as NotApplied and continue through business validation without waiting for that gap. Recovery MUST use a fresh sequence and delivery identity while preserving immutable business identity. Verified by Story 2.2-2.3.
- **FR-006**: Central-to-ship decision reports MUST be recoverable within the active session version, replaying retained reports in original sequence order without new sequence allocation or mission effects. Controls MUST NOT consume business numbers. Recovery MUST allow at most one outstanding request per session, capped at 1000 reports, and explicitly reject invalid/unavailable ranges. Diagnostics MUST expose session, version, direction, sequence, identities, outcome, reason and missing ranges. Verified by Story 2.4, 2.6 and 2.8.
- **FR-007**: Receiver sequence changes, delivery decisions, mission effects and generated reports MUST commit atomically. Resume and copied baselines MUST preserve counters/history, independent runs MUST isolate them, and stale versions MUST be rejected. Session sequence MUST NOT replace shared-capacity transactions or existing time/deadline rules. Verified by Story 2.5-2.7 and deadline cases.
- **FR-008**: Each communication class and public rule MUST occupy its own file in nested domain folders. Every module, class and public callable MUST explain What, When called, Why and Diagram. Verified by Story 4.1-4.2 and the [maintainability contract](contracts/maintainability.md).
- **FR-009**: The UML, ER and code explanations MUST agree on entity names, attributes and relationships; explanations MUST link both diagram sources. Verified by Story 4's trace.
- **FR-010**: The communication boundary and its decisions MUST have automated checks. Communication MUST depend only on shared values and the standard library, and its pure code MUST reach 100% line and branch coverage. Verified by direct tests and the declared import contract.
- **FR-011**: Existing import paths and call signatures MUST remain usable through a default local-session compatibility path. Existing unsequenced calls and the demo MUST retain their results; explicitly sequenced calls MUST follow FR-004-FR-007. Verified by regression, session-policy and demo tests.
- **FR-012**: Each mission MUST have one decision order. Central MUST register the business decisions for one mission one at a time, in central arrival order (first in, first out). Each committed decision that changes the mission history MUST receive the next mission order number, starting at 1, with no gaps or reuse. Missions MUST be ordered independently. Verified by Story 3.1-3.4.
- **FR-013**: Sender time, session sequence and delivery attempt number MUST NOT change a decision's place in the mission order. A new delivery attempt MUST enter at the back of the queue and keep its message identity. Failed transactions, replays and duplicates without effect MUST NOT consume mission order numbers. The mission order number MUST commit atomically with the decision it labels. Verified by Story 3.2, 3.5-3.6.
- **FR-014**: Decision reports and diagnostics MUST expose the mission order number next to the session sequence, so that mission history can be rebuilt across sessions and a missing decision detected. Resume and copied baselines MUST continue mission order without reuse; independent runs MUST keep separate orders. Verified by Story 3.7 and the copied-run fixtures.

### Key Entities

- **Communication message**: one ship response, with identity, request correlation, immutable content and send time; session sequence belongs to its envelope so retries can use a fresh number.
- **Delivery attempt**: one attempt to receive a message, with its own identity, attempt number, optional receipt time, session envelope, outcome and reason.
- **Delivery decision**: the named classification and explanation, without changing application state itself.
- **Communication session**: one ship's logical exchange with central in a run, with a version, independent directional counters and retained outbound reports.
- **Decision report**: central's sequenced acknowledgement of a business decision, retained for recovery without reapplying seats.
- **Mission order number**: the position of a committed decision in its mission's history, assigned by central on commit; it is the rescue counterpart of a matching engine's per-book event sequence.
- **Gap notification**: a session control identifying a missing inbound sequence range; separate from business acceptance or rejection.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every case in Stories 1, 2 and 3 has an executable acceptance check; no case changes a closed decision or counts the same confirmation twice.
- **SC-002**: All session fixtures preserve independent counters; every inbound gap reports its exact range, and every requested retained report replays with its original identity and sequence.
- **SC-003**: Duplicate sequences, fresh-sequence retries and report replays cause zero duplicate seat effects; rollback, resume, copied-run and cross-session concurrency fixtures preserve all counters and seat invariants.
- **SC-004**: Every communication module, class and public callable has the required explanation and valid UML/ER links; no file contains multiple communication classes or public rules.
- **SC-005**: All existing regression checks and the demo pass; communication reaches 100% line and branch coverage and its dependency check passes.
- **SC-006**: In every race fixture (confirmation against confirmation, cancellation against confirmation, expiry against late response), the decision registered first by central wins, and repeating the fixture gives the same order numbers and seat totals 100% of the time.
- **SC-007**: For every fixture, mission order numbers are 1..N with no gaps or reuse per mission, and replays, duplicates and failed transactions add zero numbers.

## Assumptions

- Scope is spec 007 and its supporting documents. Foundation 002 is present; this work precedes application split 008.
- The maintainer revised the choice on 2026-11-17 to the closest published B3 session policy: idempotent inbound responses and recoverable outbound reports. See the [decision and example](../../docs/architecture/communication-ordering.md) and [research](research.md).
- This is an in-memory behavioral adaptation of Binary EntryPoint 8.4.2.3. Central plays the exchange role and ships play the clients. Sequence numbers do not claim a global order across sessions.
- One in-memory run remains the shared-capacity transaction boundary. Session sequencing is the delivery-layer algorithm.
- Decision ordering follows B3's matching-engine layer, which the maintainer selected on 2026-11-17: B3 routes each order to one matching engine per market segment, queues orders first in, first out, and ranks the book by price/time priority (Binary EntryPoint 8.4.2.3, sections 2.1, 4.6.3.1 and 7.5). Here a mission plays the market segment and order book. Rescue responses have no price, so only the time half of price/time priority applies: central arrival order. Pro-rata allocation, frequent batch auctions and price-based ship ranking are not adopted; see [research](research.md). Candidate ranking by capacity and arrival estimate stays in spec 006.
- Planning must define where the mission order is stored, migration of legacy unsequenced baselines, default session mapping and recovery limits/errors; original session numbers cannot be inferred from timestamps.
- No exchange connectivity, price-based ship selection, distributed deployment, disk recovery or whole-system event replay is introduced by this feature.
- The [maintainability contract](contracts/maintainability.md) applies the requested architecture and documentation skills within the existing Spec Kit workflow and package layout.
