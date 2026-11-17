# Feature Specification: Rescue HTTP API

**Feature Branch**: `011-http-api` (planned; not created)

**Created**: 2026-11-17

**Status**: Draft

**Input**: A simple, concise server for the future visual web app, exposing all information from calls and what occurs in the solution, with minimal tasks and tests.

## Clarifications

### Session 2026-11-17

- Q: What should the web app be able to see about past calls? → A: Keep a history of every call and its result for the lifetime of the run.
- Q: Where should people be able to access the first version of the server? → A: On the same computer only, without accounts.
- Q: Should refreshing the run view also add an entry to the call history? → A: Record every call, including reads and refreshes.
- Q: How should the server record a call that reads the call history itself? → A: Store its entire response, including earlier history entries.
- Q: How should the web app stay up to date? → A: Poll the current state and read call history when needed.

## User Scenarios & Testing

### User Story 1 - Operate a rescue (Priority: P1)

A client starts a run and invokes the existing rescue operations, receiving the complete outcome of each call so it can display what happened.

**Independent Test**: Start a run, register a mission and ships, mobilise, and record responses through the interface; compare each returned outcome with the application result.

**Acceptance Scenarios**:

1. **Given** a run, **When** a client invokes an existing operation with valid input, **Then** it receives the complete result, including status, reason, identifiers and all returned data.
2. **Given** invalid input or a refused operation, **When** the client calls the interface, **Then** it receives an understandable error and previously accepted state remains unchanged.

### User Story 2 - View the run (Priority: P1)

A visual client reads the current run and its recorded activity to show the rescue's progress and explain decisions.

**Independent Test**: Execute a rescue with a partial acceptance and refusal, then retrieve its state and history and compare them with the run.

**Acceptance Scenarios**:

1. **Given** an active run, **When** a client requests its state, **Then** it can see missions, ships, availability, offers, quotes, requests, decisions, communication and recorded histories available in that run.
2. **Given** a changed run, **When** the client reads it again, **Then** the response reflects the latest committed state, including confirmed and pending seats and request outcomes.

### Edge Cases

- Unknown runs or entities return a clear not-found outcome without creating data.
- Empty collections are returned as empty collections; absent optional values remain distinguishable from zero.
- Duplicate, delayed and conflicting calls retain the existing application's identity and accounting rules.
- A failed call exposes its outcome without publishing partial business state.
- A history read returns entries completed before that read; its own complete response is recorded afterwards, avoiding self-reference.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST let a browser client create and address an isolated rescue run and invoke every public rescue application operation, including comparison and communication operations.
- **FR-002**: Every call MUST return its complete application outcome, including all available result data, status, reasons and identifiers, without silently omitting fields.
- **FR-003**: The system MUST provide a read of the latest committed run state and recorded activity, including mission progress and history, fleet and market data, requests, decisions, communication and available comparison results.
- **FR-004**: The system MUST return clear, distinguishable outcomes for malformed input, unknown resources and rejected operations; failed operations MUST preserve accepted state.
- **FR-005**: The interface MUST preserve existing rescue rules, operation identities and concurrency guarantees; transport MUST NOT implement alternative business rules.
- **FR-006**: The interface MUST exchange structured data usable by a browser and document the available operations, inputs, outputs and how to run it.
- **FR-007**: The feature MUST remain small: reuse the existing application and in-memory run, and add only the interface and reads needed for the stated client needs.
- **FR-008**: The system MUST retain and expose an ordered history of every call addressed to a run, including reads and refreshes, its input and complete success or failure result, for the lifetime of that run.
- **FR-009**: The server MUST accept connections only from the same computer by default; accounts and remote access are outside this feature.
- **FR-010**: A history read MUST return the history completed before that read, then record its entire response as its own call result.
- **FR-011**: The client MUST be able to refresh the current state and request call history independently; server-pushed updates are not required.

### Key Entities

- **Run**: An isolated rescue context containing its current state and recorded activity.
- **Operation outcome**: The full success or failure result of one call, including any returned data and identifiers.
- **Run view**: The committed rescue state and recorded histories needed to display and explain the run.
- **Call history**: The ordered inputs and outcomes of calls addressed to a run, retained for that run's lifetime.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A client can complete the existing demonstration rescue through the interface and observe 10 confirmed seats and no pending seats.
- **SC-002**: Every public application operation is callable and its returned fields are available to the client.
- **SC-003**: A client can retrieve the recorded state and activity after every step of the demonstration, including partial acceptance, refusal and further mobilisation.
- **SC-004**: Invalid input and rejected operations are reported in each tested case without changing accepted state, and the existing rescue checks continue to pass.

## Assumptions

- One server process holds isolated runs and call histories in memory; restarting it clears them. Durable storage and user accounts are outside this feature.
- The visual app is a separate later feature. It can refresh by requesting the latest state; live push and an event stream are not required.
- Existing application operations and recorded state define the information available; no new rescue simulation or business behavior is introduced. Comparison results are exposed when produced or retained, without inventing historical results.
- The plan defines the precise operation inventory, data encoding, run lifetime and browser access configuration, and selects the smallest meaningful set of tests.
- Repeated history reads can substantially increase memory usage because their complete responses are retained.
