# CLI and HTTP simulation contract

## Commands

```text
uv run python -m simulations list
uv run python -m simulations run all12 [--base-url http://127.0.0.1:8000]
uv run python -m simulations run all11
uv run python -m simulations run all10
uv run python -m simulations run baseline
uv run python -m simulations run --all
```

list performs no network calls. Names are stable. No arguments or invalid arguments print help and exit 2. Unknown profile IDs fail before creating a run. Successful selected profiles exit 0; any expectation, API or transport failure exits 1. --all executes independent profiles sequentially and continues after a profile failure. Profiles are complete one-mission executions; situation IDs are not standalone run targets. No subset editor, accounts, report files or server startup switches.

## HTTP boundary

MissionApiABC owns create_run, invoke, progress, state and invoke_batch; arguments/results are simulation models. The HTTP adapter translates those contracts and returns OperationOutcome, typed selected allocations/progress and the request/session views used by recipes. Client construction, JSON mappings, URL building, HTTPX errors and worker pool lifecycle stay in adapters/http. The CLI injects the adapter and stdout writer; services never call print, read environment variables or construct a concrete client.

Use POST /runs, POST /runs/{id}/operations/{name}, GET /runs/{id}/state. Normal observations use get_progress; state is read only when request/session evidence is needed. Do not repeatedly read API call history: it stores nested previous responses. All operations retain existing request shapes, status/reason strings and decimal encodings from [011](../../011-http-api/contracts/http-api.md).

Required operations: register_mission, register_ship, publish_availability, publish_offer, mobilise, create_request, record_response, cancel_request, expire_request, get_progress, get_session and get_deliveries. The run includes one policy EARLIEST revision 1 with selection_criteria='earliest_arrival'. No internal compare call substitutes for the external timeline.

mobilise returns a decision whose evaluations contain rank, selected, proposed_seats, revision and ship_id. For each selected evaluation submit create_request using a fresh command_id, mission_id, ship_id, proposed_seats as requested_seats, revision.revision_id, decision_id, now and explicit response_deadline. Results carry actual request IDs. A proposal is never displayed as a sent request before its create_request outcome is known.

HTTP failure or malformed response is operational failure. HTTP 200 containing application status='rejected' remains a normal observable result if expected by a situation. A timeout after a write is 'outcome unknown'; do not retry or claim unchanged state. Parse instants as Decimal, never float. Disable automatic retries and proxy environment use; connect/pool timeouts 2s, read/write 10s. At most two clients/workers in a concurrent batch, closed after joining. The server serializes requests per run; this demonstrates competing clients and preserved accounting, not parallel domain commits.

## Transcript

Emit lines while execution progresses, not only after it ends. Each line includes local ordinal, virtual t, profile/mission ID, event or batch ID, action, available decision/request/ship IDs, requested or confirmed quantity, status and reason. After an event/solver round print demand, confirmed, pending, additional_needed and mission status from get_progress. Log calls as sent and completed, including rejected negative probes and read operations; do not imply observation reads changed seats.

Concurrent submissions have submission slots and a batch ID. Display returned results with those identifiers; do not claim their display order is server commit order. Show authoritative progress after joining. Decimal virtual time, per-session message sequence and local transcript ordinal are separate fields.

Final line: profile, pass/fail, observed/declared situations, mission status, confirmed, pending and unconfirmed. Missing observations are marked unavailable. Show missing situation IDs or failed expectations. A passed profile can have an intentionally incomplete mission.

## Interface repair acceptance

Before relying on this contract, valid nested publish_availability, publish_offer and record_response payloads must decode without NameError. Use an explicit trusted runtime type namespace in the API codec for TYPE_CHECKING-only nested annotation names; preserve unknown-field validation and existing result shapes. Add HTTP regression coverage at tests/integration/api/http/test_nested_commands.py. The runner cannot work around this by importing application contracts or bypassing HTTP.
