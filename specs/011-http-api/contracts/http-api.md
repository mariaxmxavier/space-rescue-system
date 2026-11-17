# HTTP contract

JSON requests and responses. Bind to `127.0.0.1`; allow configured local browser origins and reject untrusted origins on state-changing requests. No accounts or remote service exposure.

| Method and path | Purpose |
|---|---|
| `POST /runs` | Create a run from `application_run_id`, `central_id`, and optional `policies` and `scenarios`. Return its IDs. |
| `GET /runs/{run_id}/state` | Return complete committed state. |
| `GET /runs/{run_id}/history` | Return earlier completed call entries, then record this response. |
| `POST /runs/{run_id}/operations/{operation}` | Execute an explicitly registered public facade operation; body contains its named arguments. Return all `Result` fields. |

Operations: `register_mission`, `register_ship`, `publish_availability`, `publish_offer`, `request_quotes`, `record_quote`, `accept_quote`, `create_request`, `reject_quote`, `expire_quotes`, `cancel_request`, `expire_request`, `record_response`, `recover_reports`, `synchronise_inbound`, `get_session`, `get_progress`, `get_history`, `get_decision`, `get_deliveries`, `compare`, `mobilise`. Define schemas from actual signatures and nested types, including policy and scenario inputs; publish them in API documentation.

Use 201 for creation, 200 for application results including rejected outcomes, 400 for malformed JSON or invalid arguments, 404 for unknown run or operation, and 409 for duplicate run. Errors have a `detail` field. Record every request addressed to a known run, including validation errors and reads; creation and unknown-run requests cannot be attached to an existing run. Serialize each known-run request through a per-run lock, including history reads; assign sequence and append after constructing the response. A history read records the exact earlier snapshot returned. Never silently drop fields or convert decimals to floats.
