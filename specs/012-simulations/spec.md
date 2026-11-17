# Feature Specification: Composed Mission Simulations

**Feature Branch**: `012-simulations` (planned; checkout remains main)
**Created**: 2026-11-17
**Status**: Ready for planning
**Input**: One simulation follows one mission's full timeline as the solver runs. Combine the twelve situations in that mission, then run variants containing eleven, ten or fewer. Keep output concise and group reusable situations in folders/subfolders.

## Clarifications

- 2026-11-17: Situations are reusable ingredients, not twelve separate simulations. They occur at suitable points in one mission timeline; they need not happen at the same instant.
- Selected output: terminal walkthrough and final summary, without saved reports.

## User Scenarios & Testing

### User Story 1 - Follow a complete combined timeline (Priority: P1)

A person runs one mission containing all twelve situations and watches the solver decide, send requests, receive responses and seek more help until all scheduled events are accounted for.

**Why this priority**: Shows the whole rescue described in sections 3-6 of the [original problem](../../docs/context/original-problem.md), rather than isolated rule demonstrations.
**Independent Test**: Run the all-twelve timeline for ten people; verify every declared situation was observed within that same mission and finish with ten confirmed, zero pending seats.

**Acceptance Scenarios**:

1. **Given** one mission and a composed scenario, **When** the simulation runs, **Then** one chronological walkthrough shows setup, solver decisions, selected requests, responses, closures, delivery outcomes and progress.
2. **Given** a partial confirmation, refusal or closed pending request, **When** demand becomes uncovered, **Then** the solver is invoked again and its selections drive further requests.
3. **Given** temporary insufficient capacity, **When** availability later improves, **Then** the same mission visibly progresses from shortfall to further mobilisation and completion.
4. **Given** a completed mission with scheduled late deliveries, **When** those deliveries occur, **Then** they are shown and checked without opening unnecessary requests or changing settled outcomes.

### User Story 2 - Change the combination (Priority: P1)

A person selects a scenario variant combining eleven, ten or fewer situations while retaining a complete mission timeline.

**Why this priority**: Demonstrates how combinations affect the solver's execution without creating a separate simulator for every rule.
**Independent Test**: Run all-twelve, eleven-situation and ten-situation profiles; each has one isolated mission, declared included situations and evidence of every included situation.

**Acceptance Scenarios**:

1. **Given** reusable situation definitions, **When** profiles select different combinations, **Then** the same runner executes each profile with independent state and fresh identities.
2. **Given** a profile, **When** it is listed or started, **Then** its included situations, count and expected final outcome are visible.
3. **Given** a declared situation never triggered, **When** the timeline ends, **Then** the scenario fails and names the missing evidence.
4. **Given** a scenario intended to end with a shortfall, **When** its expected final state is observed, **Then** the scenario passes while the mission remains incomplete.

### User Story 3 - Read and verify the execution (Priority: P2)

A person follows every operation and understands how the mission reached its final state.

**Why this priority**: Makes solver decisions and rescue commitments explainable.
**Independent Test**: Read the transcript and identify each request's ship, requested quantity, response, closure and seat changes, followed by a clear scenario result.

**Acceptance Scenarios**:

1. **Given** an event or solver round, **When** it executes, **Then** output shows logical time, action, result/reason and confirmed, pending and unmet demand.
2. **Given** concurrent submissions, **When** their results return, **Then** each is identified and accounting is checked without assuming which wins.
3. **Given** an unexpected result, **When** an expectation fails, **Then** the failed action and expected versus observed outcome are visible and execution signals failure.

### Situation Catalogue

| Group | Subgroup | Situation |
|-------|----------|-----------|
| rescue | completion | Full confirmation |
| rescue | remobilisation | Partial confirmation and refusal |
| requests | closure | Cancellation; expiration |
| communication | delivery | Duplicate response; delayed response |
| communication | ordering | Out-of-order responses |
| safety | validation | Invalid quantities |
| safety | finality | Response to a closed request |
| safety | concurrency | Simultaneous operations |
| availability | shortfall | Insufficient capacity |
| availability | updates | Changed availability |

These twelve situations are composed into scenario timelines, not exposed as twelve standalone mission simulations.

### Edge Cases

- Unknown profiles or incompatible combinations fail before creating a run.
- Transport failure ends the scenario with a clear error; uncertain writes are not silently resent.
- Concurrent winners may vary; permitted outcomes and invariants determine success.
- Untriggered events, exhausted event budgets and unresolved pending requests are reported rather than silently treated as completion.
- Repeating a profile cannot collide with earlier server state.

## Requirements

### Functional Requirements

- **FR-001**: Users MUST list composed profiles, run one or run all; each execution MUST use one isolated run containing one mission.
- **FR-002**: The system MUST provide profiles combining all twelve, eleven, ten and a smaller baseline set of situations. Each MUST declare its included situations and expected final state; exhaustive combinations are excluded.
- **FR-003**: Requests MUST follow actual solver selections obtained through spec 011. The runner MUST repeat solver rounds when mission or fleet changes require reconsideration, without implementing its own allocation strategy.
- **FR-004**: One continuous timeline MUST show every operation, solver decision and request, including ship, seats, request/decision identities, response or closure, delivery outcome and available reasons.
- **FR-005**: Each event/solver round MUST show logical time, confirmed seats, pending seats and unmet demand (demand minus confirmed minus pending). Final output MUST also show remaining unconfirmed seats (demand minus confirmed).
- **FR-006**: Every declared situation MUST have observed evidence within the same mission. Missing evidence MUST fail the scenario even if the mission completes.
- **FR-007**: Simulation events MUST support delayed, repeated and reordered deliveries, explicit cancellation/expiration, invalid attempts, availability updates and concurrent submissions while preserving accepted rescue data.
- **FR-008**: Mission completion MUST require confirmed seats equal demand. It MUST stop unnecessary mobilisation but MUST NOT skip already scheduled demonstration events.
- **FR-009**: Each scenario MUST check expectations and end with pass/fail, observed situation count and final mission status. Expected incompleteness MUST remain distinct from scenario failure; any failed selected scenario MUST give the overall command a failing result.
- **FR-010**: Reusable situations MUST be grouped by the catalogue's group/subgroup. Scenario composition, execution, transport and terminal presentation MUST remain separate, with common behavior defined once.
- **FR-011**: Instructions MUST explain server prerequisites, profiles and combinations, repeated runs, transcript fields and verification.
- **FR-012**: This feature MUST preserve rescue rules and use HTTP for all system interactions. A prerequisite interface repair is permitted only to make existing operations callable without changing their business semantics.

### Key Entities

- **Scenario profile**: One mission's initial fleet, policy, included situations, timeline and expected result.
- **Situation**: Reusable trigger, action and evidence definition belonging to a group/subgroup.
- **Timeline event**: Logical time, stable ordering, action and references to observed requests or decisions.
- **Observation**: Actual operation outcome, progress and situation evidence.
- **Scenario result**: Expected-versus-observed checks, coverage of included situations and final mission state.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The comprehensive timeline observes all twelve situations within one ten-person mission and ends at ten confirmed, zero pending seats.
- **SC-002**: Eleven- and ten-situation profiles observe exactly their declared situation sets, retaining complete mission timelines.
- **SC-003**: Every operation/request is traceable in chronological output; each event/solver round includes progress.
- **SC-004**: Repeated runs satisfy the same business expectations without state interference or false failures from concurrent ordering.
- **SC-005**: Missing evidence, unexpected outcomes and transport failures always produce explicit scenario failure; expected shortfalls remain distinguishable.

## Assumptions

- The user starts the local spec 011 server. Simulations accept its address and never start it automatically.
- Times and events are scripted; no wall-clock sleeps, flights, boarding, routes or storm simulation.
- A fixed small catalogue provides all12/all11/all10/baseline combinations. A generic combination editor and every possible subset are outside scope.
- Insufficient capacity may be a temporary phase in a completed mission; full and partial responses occur on different requests.
- Clean Architecture and Cosmic Python guide implementation; the current HTTP adapter's nested-payload decoding must be repaired and verified first.
