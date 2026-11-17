# Operation Field Inventory

Source of truth: `rescue/api/operations.py`, command dataclasses under `rescue/application/contracts/commands/`, `rescue/api/codec.py`, and nested model dataclasses. Unknown fields are rejected. Command operation body shape is exactly `{ "command": { ... } }`; scalar operations use only the listed top-level keys. Optional fields may be omitted or set to `null` where their annotations allow it.

## Run endpoints

- `POST /runs`: required `application_run_id: string`, `central_id: string`; optional `policies: MobilisationPolicy[]`, `scenarios: RescueScenario[]`.
- `GET /runs/{run_id}/state`: no body.
- `GET /runs/{run_id}/history`: no body; fetch on user request only.

## Operations

| Operation | Body | Fields |
| --- | --- | --- |
| `register_mission` | command | `mission_id: string`, `station_name: string`, `people_count: integer`, `created_at: decimal string` |
| `register_ship` | command | `ship_id: string`, `name: string` |
| `publish_availability` | command | `availability: ShipAvailability` |
| `publish_offer` | command | `offer_id: string`, `mission_id: string`, `ship_id: string`, `revision: ShipOfferRevision` |
| `request_quotes` | command | `mission_id: string`, `now: decimal string`, optional `response_deadline: decimal string|null` |
| `record_quote` | command | `offer: RFQOffer`, `now: decimal string` |
| `accept_quote` | command | `command_id: string`, `mission_id: string`, `quote_id: string`, `now: decimal string`, optional `response_deadline: decimal string|null`, `decision_id: string|null`, `revision_id: string|null` |
| `create_request` | command | `command_id: string`, `mission_id: string`, `ship_id: string`, `requested_seats: integer`, `revision_id: string`, `now: decimal string`, optional `response_deadline: decimal string|null`, `decision_id: string|null` |
| `reject_quote` | command | `quote_id: string`, `now: decimal string` |
| `expire_quotes` | scalar | `now: decimal string or integer` |
| `cancel_request` | command | `mission_id: string`, `request_id: string`, `now: decimal string` |
| `expire_request` | command | `mission_id: string`, `request_id: string`, `now: decimal string` |
| `record_response` | command | `message_id: string`, `delivery_id: string`, `attempt_number: integer`, `request_id: string`, `outcome: string`, `confirmed_seats: integer`, `sent_at: decimal string`, `received_at: decimal string|null`, optional `communication_rtt_seconds: decimal string|null`, `envelope: SessionEnvelope|null` |
| `recover_reports` | command | `session_id: string`, `version: integer`, `from_sequence: integer`, `count: integer` |
| `synchronise_inbound` | command | `session_id: string`, `version: integer`, `next_sequence: integer` |
| `get_session` | scalar | `session_id: string` |
| `get_progress` | scalar | `mission_id: string`, `now: decimal string or integer` |
| `get_history` | scalar | `mission_id: string` |
| `get_decision` | scalar | `decision_id: string` |
| `get_deliveries` | scalar | `message_id: string` |
| `compare` | command | `scenario_id: string`, `scenario_revision: integer`, `policy_keys: [[policy_id: string, revision: integer], ...]` |
| `mobilise` | command | `mission_id: string`, `policy_id: string`, `policy_revision: integer`, `now: decimal string` |

## Nested values

- `ShipAvailability`: `availability_id: string`, `ship_id: string`, `total_seats: integer`, `arrival_estimate_seconds: decimal string`, `available: boolean`, `recorded_at: decimal string`.
- `ShipOfferRevision`: `revision_id: string`, `revision_number: integer`, `capacity: integer`, `arrival_estimate_seconds: decimal string`, `available: boolean`, `recorded_at: decimal string`.
- `RFQOffer`: `offer_id: string`, `rfq_id: string`, `offered_seats: integer`, `arrival_estimate_seconds: decimal string`, `expires_at: decimal string`, `recorded_at: decimal string`, optional `status: QuoteStatus` (defaults `HELD`), optional `request_id: string|null` (normally omit for a new quote). Status is the enum value in `rescue/market/models/quotes/quote_status.py`.
- `SessionEnvelope`: `session_id: string`, `version: integer`, `direction: FlowDirection`, `sequence: integer`. Enum values are defined in `rescue/communication/models/vocabulary/flow_direction.py`.
- `MobilisationPolicy`: `policy_id: string`, `revision: integer`, `name: string`, `selection_criteria: string or object of string key/value criteria`; it must name a supported strategy from `rescue/mobilisation/models/algorithm_name.py`.
- `RescueScenario`: required `scenario_id: string`, `revision: integer`, `name: string`, `baseline: RunBaseline`, `response_rules: ScriptedResponse[]`, `availability_changes: ShipAvailability[]`, `time_horizon_seconds: decimal string`, `seed: nonnegative integer`, `event_budget: positive integer`; optional `communication_profiles: CommunicationProfile[]` (defaults empty).
- `RunBaseline`: `missions` array and `market` object; optional `command_index`, `message_index`, `delivery_index`, `decision_index`, and `session_index` arrays default empty. Mission and market nested shapes come from their dataclasses under `rescue/mission/models/` and `rescue/market/models/`.
- `ScriptedResponse`: `ship_id: string`, `request_ordinal: positive integer`, `outcome: RequestOutcome` (`ACCEPTED`, `PARTIALLY_ACCEPTED`, `REFUSED`), optional `confirmed_seats: nonnegative integer|null`.
- `CommunicationProfile`: `profile_id: string`, `ship_id: string`, `outbound_delay_seconds: decimal string`, `decision_delay_seconds: decimal string`, `return_delay_seconds: decimal string`; optional ordinal arrays `loss_rule`, `duplication_rule`, `reordering_rule` (default empty).
- `RunBaseline.market`: `market_id: string`; optional empty arrays `ships`, `availabilities`, `rfqs`, `quotes`, `offers`, `quote_history`. `Ship` fields: inspect `rescue/market/models/fleet/ship.py`; other market values use the corresponding model dataclass fields. `RunBaseline.missions` contains mission model objects; inspect `rescue/mission/models/mission/mission.py` and its nested value types.

## Encoding and outcomes

- `Decimal` must be encoded as a finite decimal string or integer. JSON floating-point numbers are rejected. Decimal results serialize as strings.
- Tuples serialize as arrays; fixed tuples require the exact length. Enums use their string values. Dataclasses use object fields. Extra fields and missing required fields are rejected.
- On HTTP 200, inspect application result `status`, `value`, and `reason`; business rejection does not necessarily use a non-200 HTTP status. Preserve and expose the complete result object.
- Full nested scenario and baseline controls must derive from source dataclass fields recursively; do not make users hand-author JSON. Validate every field and enum against constructors and a real API call before publishing the UI.
