# Feature Specification: Rescue Web App

**Feature Branch**: `013-web-app` (proposed; not created)

**Created**: 2026-11-17

**Status**: Draft

**Input**: Start roadmap feature 013: a web UI through which users can do everything the existing solution does. Use UI/UX Pro Max, Clean Architecture, Cosmic Python and brainstorming; organise use cases in folders and subfolders; ground the feature in the original rescue problem.

## User Scenarios & Testing

### User Story 1 - Coordinate a rescue in the browser (Priority: P1)

An operator starts a run, registers a mission and ships, publishes capacity and offers, requests help, records ship responses and continues mobilisation until every person has confirmed transport.

**Why this priority**: This is the original problem's end-to-end rescue workflow.

**Independent Test**: Complete the demonstration entirely in the browser, including partial acceptance, refusal and further mobilisation.

**Acceptance Scenarios**:

1. **Given** a new run, **When** the operator registers a station, positive rescue demand and ships with availability and arrival estimates, **Then** the registered records and their identifiers are visible in that run.
2. **Given** available offers, **When** the operator mobilises or creates a seat request, **Then** the requested seats, affected ship and full operation outcome are visible.
3. **Given** pending requests, **When** the operator records full acceptance, partial acceptance or refusal, **Then** confirmed, pending and still-unrequested demand reflect the accepted outcome, and partial acceptance closes that request.
4. **Given** remaining demand after partial acceptance and refusal, **When** the operator requests further help and receives sufficient confirmations, **Then** completion appears only when confirmed seats equal demand.
5. **Given** a pending request, **When** the operator cancels or expires it, **Then** its final outcome and released pending seats appear; later responses cannot change that outcome.

### User Story 2 - Understand the current run and every outcome (Priority: P1)

An operator inspects progress, related records, decisions and recorded calls to understand what is guaranteed, what is outstanding and why an action succeeded or failed.

**Why this priority**: Reliable coordination requires distinguishing confirmed transport from pending requests and temporary holds.

**Independent Test**: Inspect a prepared run containing all request outcomes, a rejected operation and a mobilisation decision; compare the displayed data with the authoritative run records.

**Acceptance Scenarios**:

1. **Given** a mission, **When** the operator opens its progress, **Then** demand, confirmed seats, pending seats, unmet demand, timing and status are separately labelled.
2. **Given** a decision, **When** the operator inspects it, **Then** available allocations, candidate evaluations, reasons and trace details can be read without omitting returned fields.
3. **Given** completed calls, **When** the operator opens call history, **Then** order, submitted input, success or failure and complete returned content are inspectable, separately from mission history.
4. **Given** state changed by another browser view, **When** the current view refreshes, **Then** it shows the latest committed state and the time of the successful refresh.

### User Story 3 - Manage quotes and shared capacity (Priority: P2)

An operator requests and records quotes, accepts or rejects them, expires stale quotes and revises availability without confusing held capacity with confirmed transport.

**Why this priority**: These existing market capabilities must remain usable beyond the basic demonstration.

**Independent Test**: Use two missions and one shared ship; hold a quote, accept or release it, and inspect the capacity commitments and operation outcomes.

**Acceptance Scenarios**:

1. **Given** registered ships and missions, **When** the operator requests and records quotes, **Then** requests for quote, offered quantities, validity and hold status are visible.
2. **Given** an active quote, **When** the operator accepts, rejects or expires it, **Then** the resulting request or released hold and full outcome appear.
3. **Given** competing missions, **When** an action exceeds available capacity, **Then** the rejection and reason appear while accepted commitments remain unchanged.
4. **Given** revised availability or offers, **When** the operator inspects the ship and mission, **Then** the latest version and available revision history are distinguishable from earlier records.

### User Story 4 - Exercise communication and recovery (Priority: P2)

A user reproduces unreliable communication and inspects how duplicate, delayed and out-of-order responses are handled, including session synchronisation and report recovery.

**Why this priority**: The original problem explicitly requires reliable operations when communication misbehaves.

**Independent Test**: Submit duplicate and out-of-order responses, inspect delivery classifications and session state, synchronise an inbound sequence and recover reports through browser controls.

**Acceptance Scenarios**:

1. **Given** a response, **When** the user supplies message and session identifiers, sequence and timing values supported by the existing operation, **Then** the complete delivery and business outcome is visible.
2. **Given** a repeated, late or out-of-order message, **When** it is submitted, **Then** its classification and reason appear without falsely changing confirmed seats or closed outcomes.
3. **Given** a session gap or recoverable reports, **When** the user inspects the session and invokes synchronisation or recovery, **Then** sequence state, control outcome and returned reports are inspectable without repeating seat effects.

### User Story 5 - Compare strategies and scenarios (Priority: P2)

A user supplies policies and scenarios at run creation, executes supported comparisons and inspects each returned run and its explanation.

**Why this priority**: Full capability coverage includes the existing experiments functionality.

**Independent Test**: Configure one supported scenario and at least two policies, execute a comparison, and inspect every returned result and timeline.

**Acceptance Scenarios**:

1. **Given** supported policy and scenario settings, **When** the user creates a run and compares selected policies, **Then** every returned result, summary, identifier and timeline is inspectable and linked to its configuration.
2. **Given** no configured scenarios or invalid settings, **When** the user attempts comparison, **Then** an actionable explanation appears without fabricated results.

### Edge Cases

- Missing or invalid quantities, identifiers, timing values and required fields show understandable feedback and preserve entered values for correction.
- Unknown run or entity identifiers show a distinguishable unavailable result; a lost in-memory run is not silently recreated.
- Empty collections, absent optional values and zero quantities remain distinguishable.
- A connection failure leaves the last successful snapshot visibly stale; a command with an uncertain outcome is not automatically repeated under a new identity.
- Switching runs while a call is outstanding cannot place its response into the newly selected run.
- Consecutive refreshes cannot replace newer displayed state with an older response.
- Repeated history reads include previous history responses; loading history is explicit and separate from routine state refreshes.
- Long histories and deeply nested outcomes remain inspectable through expandable details without automatically expanding every record.
- Long identifiers and narrow screens do not hide actions or essential quantities.

## Requirements

### Functional Requirements

- **FR-001**: Users MUST be able to create an isolated run, supply its supported policy and scenario configuration, reopen a known run by identifier and switch between known runs without mixing their data.
- **FR-002**: Every existing public rescue operation MUST have a discoverable browser action with labelled input controls and complete outcome inspection. Users MUST NOT need a terminal or separately authored request document to complete a supported operation.
- **FR-003**: The UI MUST support mission registration and progress, ship registration, availability and offer revisions, mobilisation and direct seat requests.
- **FR-004**: The UI MUST support full and partial responses, refusal, cancellation and expiration, displaying final outcomes and the effects on demand.
- **FR-005**: The UI MUST support quote requests, quote recording, acceptance, rejection and expiry, and distinguish temporary holds, pending commitments and confirmed transport.
- **FR-006**: The UI MUST support communication delivery inspection, session inspection, inbound synchronisation and report recovery, including the existing identity, sequence and timing inputs.
- **FR-007**: The UI MUST support policy/scenario configuration and comparison, including inspection of complete returned results and retained experiment records.
- **FR-008**: Users MUST be able to inspect all available committed run data, mission history, decisions, messages, deliveries, sessions and call history. Human-readable summaries MAY use expandable structured details to preserve all returned fields.
- **FR-009**: Mission views MUST separately display total demand, confirmed seats, pending seats, unmet demand and authoritative status. Holds and pending seats MUST NOT be presented as confirmed transport.
- **FR-010**: Routine state refresh MUST be independent of explicit call-history loading. Users MUST see loading, empty, success, rejected, unavailable and connection-failure states, with the last successful refresh time.
- **FR-011**: Submissions MUST preserve operation identity, prevent accidental repeat submission while pending and display complete success or rejection reasons. An uncertain network outcome MUST be shown without automatic mutation retries.
- **FR-012**: All primary workflows MUST be usable by keyboard, with visible focus, labelled controls, readable errors and status distinctions that do not rely on colour alone. Reduced-motion preferences MUST be respected.
- **FR-013**: Navigation and primary forms MUST remain usable at viewport widths from 360 to 1440 pixels; wide records MAY use a labelled scrollable detail region while primary actions remain reachable.
- **FR-014**: The browser MUST use the existing rescue rules and accepted outcomes as its authority; presentation MUST NOT independently decide capacity, request finality, message classification or strategy allocation.
- **FR-015**: Documentation MUST explain how to launch the app locally, connect it to a run and complete the demonstration and advanced workflows, including the loss of in-memory runs after server restart.
- **FR-016**: The rescue operations and exploration tabs MUST share the same selected main run. Exploration MUST distinguish the live run from comparisons based on configured simulation scenarios.

### Key Entities

- **Run workspace**: The selected rescue context, configuration, current records and refresh status.
- **Mission view**: Station, demand, authoritative progress and related requests, offers, quotes and decisions.
- **Fleet and market view**: Ships, availability, offer revisions, quote requests, quotes and capacity commitments.
- **Communication view**: Messages, delivery classifications, session sequence state and recoverable reports.
- **Experiment view**: Policies, scenarios, comparison results, summaries and timelines.
- **Activity record**: An ordered call with its submitted input and complete outcome, distinct from mission history.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A user completes the existing ten-person demonstration entirely in the browser, including partial acceptance, refusal and further mobilisation, ending with ten confirmed seats and zero pending seats.
- **SC-002**: A capability review demonstrates browser input and complete result inspection for 100% of the public operations inventoried at planning time, including all 22 currently exposed operations and run creation, state and call-history access.
- **SC-003**: For every demonstration step, displayed seat totals, final outcomes and decision reasons match the authoritative records; no pending or held seats are labelled confirmed.
- **SC-004**: A user completes each of the five story verification journeys without terminal commands or hand-authoring a request document after application startup.
- **SC-005**: All primary forms and actions are usable with keyboard alone at both 360-pixel and 1440-pixel widths; labels, focus and error feedback remain available.
- **SC-006**: In the unavailable-server, invalid-input, rejected-operation and lost-run verification cases, the user sees a distinguishable explanation and accepted rescue data remains unchanged.

## Assumptions

- This is roadmap feature 013, dependent on implemented feature 011. It does not depend on the separate feature 012 simulation client; the explicit roadmap number takes precedence over automatic next-directory numbering.
- The app supports rescue operators and people exploring algorithms and communication in separate tabs sharing the main run. Guided forms for all operations are the planned approach.
- The original problem and constitution bound the rescue at reservation confirmation. Flights, boarding, routing, storm simulation and fleet optimisation are excluded.
- Existing runs and call histories remain in memory. User accounts, remote hosting and durable persistence are excluded; reopening uses a known run identifier because automatic discovery is not currently provided.
- English UI text is the initial default. Visual style and detailed screen organisation remain design decisions.
- Capability coverage means existing application operations, supplied configurations, outcomes and inspectable state; it does not imply exposing private functions, arbitrary code execution or inventing new rescue behaviour.
