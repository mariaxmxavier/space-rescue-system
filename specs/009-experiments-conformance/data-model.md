# Data Model: Experiments Conformance

Fields do not change; they only move to one file per class. The diagrams follow these tables
(research R7).

## Scenario (`rescue/experiments/models/scenario/`)

| Class | Fields | Owned by |
|-------|--------|----------|
| `RescueScenario` (aggregate) | `scenario_id`, `revision`, `name`, `baseline: RunBaseline`, `response_rules: tuple[ScriptedResponse]`, `availability_changes: tuple[ShipAvailability]`, `time_horizon_seconds`, `seed`, `event_budget`, `communication_profiles: tuple[CommunicationProfile] = ()` | itself |
| `RunBaseline` | `missions: tuple[Mission]`, `market: B3Market`, `command_index`, `message_index`, `delivery_index`, `decision_index` | RescueScenario, 1 |
| `ScriptedResponse` | `ship_id`, `request_ordinal`, `outcome`, `confirmed_seats = None` | RescueScenario, 0..* |
| `CommunicationProfile` | `profile_id`, `ship_id`, `outbound_delay_seconds`, `decision_delay_seconds`, `return_delay_seconds`, `loss_rule`, `duplication_rule`, `reordering_rule` | RescueScenario, 0..* |

## Run (`rescue/experiments/models/run/`)

| Class | Fields | Relation |
|-------|--------|----------|
| `SimulationRun` | `run_id`, `scenario_id`, `scenario_revision`, `policy_id`, `policy_revision`, `started_at`, `finished_at`, `status`, `result: SimulationResult \| None` | uses one RescueScenario revision and one MobilisationPolicy revision |
| `SimulationResult` | `completed`, `confirmed_seats`, `unmet_demand`, `requests_sent`, `released_seats`, `confirmation_elapsed_seconds`, `latest_arrival_estimate_seconds` | SimulationRun, 0..1 |
| `RunSnapshot` | `run: SimulationRun`, `missions`, `market`, the four indexes | wraps one SimulationRun |

`SimulationRun.status`: `horizon_reached` → `completed` when all missions reach `C = D` before
the next event instant. These literals stay as they are (out of scope, spec Assumptions).

## Timeline (`rescue/experiments/timeline/`)

| Class | Fields / behaviour |
|-------|--------------------|
| `TimelineEvent` | `instant`, `kind` (`mobilise` \| `availability` \| `expire` \| `response`), `scenario_sequence`, `payload = None`, `priority = None` (resolves to 0 for `expire`, else 1) |
| `Timeline` | heap ordered by `(instant, priority, scenario_sequence, insertion order)`; `peek_next`/`pop_next` return `None` past the horizon; the `event_budget + 1`th `schedule` raises `DomainValidationError` |

## Simulation (`rescue/experiments/simulation/`): run-time only, not persisted

| Name | Kind | Holds |
|------|------|-------|
| `StartRun` | Protocol (port) | `(application_run_id, central_id, *, policies, scenarios, reserved_ids) -> RunHandle` |
| `RunHandle` | Protocol (port) | `store: TransactionStore`, `id_source: IdSource`, `central: SimulationCentral` |
| `SimulationCentral` | Protocol (port) | `mobilise`, `create_request`, `publish_availability`, `expire_request`, `record_response` |
| `SimulationSession` | frozen dataclass | `handle`, `policy`, `timeline`, `rng`, `sequence`, `response_rules`, `profiles`, `ship_ordinals` (research R3) |
| `_ResponsePayload` | private frozen dataclass | message id, mission id, request id, outcome, seats, attempt, sent and received instants, RTT |

## Validation (unchanged, moved)

- Every model keeps its `__post_init__` checks. `_frozen_tree` and `_finite_tuple` move to
  `models/_validation.py`.
- `simulate` still rejects a non-`RescueScenario`, a non-`MobilisationPolicy`, a baseline with no
  missions, and now a non-callable `start_run`, all with `DomainValidationError`.
