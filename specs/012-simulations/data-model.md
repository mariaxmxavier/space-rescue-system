# Simulation data model

All contracts are local simulation types, one class per file under simulations/models/. They do not import rescue or HTTPX. Use a shared immutable BaseModel with extra='forbid', frozen=True and strict=True; tuple collections. Convert JSON times/enums at the HTTP edge once. Boundary wire models can preserve fields not used by simulation logic without forwarding raw dictionaries inward.

| Type | Fields and constraints | Purpose |
|------|------------------------|---------|
| SituationId | enum with exactly the twelve IDs below | Evidence identity, never inferred from displayed labels |
| ScenarioProfile | nonblank scenario_id; one MissionSetup; tuple ShipSetup; PolicySetup; unique included SituationIds; tuple recipes; FinalExpectation; event_budget=200; horizon=Decimal('100') | One mission's complete composition |
| MissionSetup | station_name nonblank; demand positive integer excluding bool | Mission data; built-ins demand=10 |
| ShipSetup | symbolic ship key; name; capacity nonnegative integer; arrival finite Decimal>=0; offer revision positive | Server setup data |
| SituationRecipe | SituationId; trigger; typed action; evidence predicate; optional dependencies | Reusable scenario ingredient |
| RequestSelector | symbolic ship key; request occurrence positive integer | Binds returned IDs, never predicts them |
| TimelineEvent | event_id nonblank; time finite Decimal>=0; phase enum; ordinal unique integer>=0; discriminated action | Heap key (time, phase, ordinal) |
| Action | union: PublishFleet, SolverRound (submit bool), ShipReply, CloseRequest, ConcurrentRequests, Observe | Semantic instructions; proposal-only recovery rounds are explicitly labelled |
| SelectedAllocation | decision_id; evaluation_id; rank>0; ship_id; proposed_seats>0; revision_id | Typed projection of solver output |
| MissionProgress | mission_id; demand; confirmed; pending; unconfirmed; additional_needed; status | API-owned progress; not a replacement domain model |
| OperationOutcome | operation enum; HTTP status; application status/reason when present; typed operation value; identifiers | Distinguishes HTTP failure and business rejection |
| Observation | ordinal; logical time; event/batch ID; operation outcome; progress or unavailable marker; tuple Evidence | Immutable transcript record |
| Evidence | situation ID; triggering event IDs; check name; expected; observed; matched bool | Proves declared situations actually happened |
| FinalExpectation | expected mission status; confirmed/pending/unconfirmed integers>=0; required situation set | Allows intentional shortfall |
| ScenarioResult | profile ID; actual run/mission IDs; pass/fail; matched/missing situation IDs; last observed progress; failure detail optional | Summary independent of mission completion |
| RunOptions | base_url; selected profile IDs; positive HTTP phase timeouts | Supplied by entrypoint, no environment access in models/services |

Evidence expected/observed values are typed scalar or tuple-of-scalar projections, not unstructured maps. Models validate their shape; only expectation checks compare server state. Invalid-quantity probes use valid typed envelopes with deliberately invalid business values (e.g. confirming three seats on a two-seat request), not construction-invalid local models.

## Situation vocabulary

full_confirmation; partial_and_refusal; cancellation; expiration; duplicate_response; delayed_response; out_of_order; invalid_quantity; closed_request_response; simultaneous_operations; insufficient_capacity; availability_change.

Group/subgroup mapping is owned by the spec catalogue. Each situation module supplies a recipe and explicit evidence conditions; it does not send HTTP or implement a competing solver. A recipe can reference a request selector; the runner resolves the selector only after observing a real created request. Missing bindings or dependencies fail the scenario explicitly.

## Execution transitions

Prepared -> Running -> Passed or Failed. Mission completion is an observation inside Running, not a runner terminal state. Setup creates one run and one mission with a fresh execution namespace (UUID prefix generated at the entrypoint). All command/message/delivery IDs remain unique within that namespace except intentional message replay.

Event phases: fleet changes, closures, deliveries/probes, solver round. At equal time, closures precede deliveries; ordinal resolves ties within a phase. After each event, observe progress. Batch members share a time and batch ID; progress describes the joined batch, not fabricated intermediate states. Schedule one solver reconsideration after an instant/batch with relevant changes. No future event plus unmet demand produces an explicit expected-incomplete result or failure according to FinalExpectation.

Session sequences are scoped by session/version/direction. A repeated message reuses message_id and payload with a new delivery_id and higher attempt_number. A corrected rejected payload uses a new message and next sequence. Out-of-order evidence requires an observed gap/duplicate_sequence disposition, not merely a shuffled transcript. See the [timeline contract](contracts/timeline.md).
