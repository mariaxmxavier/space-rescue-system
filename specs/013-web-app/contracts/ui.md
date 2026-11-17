# Browser UI Contract

## Shared workspace

Operations and Exploration share the selected run and its committed snapshot. Switching runs invalidates outstanding responses. Create a run with identifiers and supported policy/scenario configuration; reopen by known ID. Show unknown or lost runs clearly. Refresh state separately from explicit history reads and show the last successful refresh and stale state. Disable duplicate submissions while pending and report uncertain outcomes without resubmission.

## Capability inventory

| Area | Operations |
| --- | --- |
| Missions | `register_mission`, `get_progress`, `get_history` |
| Fleet | `register_ship`, `publish_availability`, `publish_offer` |
| Quotes | `request_quotes`, `record_quote`, `accept_quote`, `reject_quote`, `expire_quotes` |
| Requests | `create_request`, `cancel_request`, `expire_request` |
| Mobilisation | `mobilise`, `get_decision` |
| Communication | `record_response`, `get_deliveries`, `get_session`, `synchronise_inbound`, `recover_reports` |
| Comparison | `compare` |

Each operation has discoverable labelled controls covering supported input and complete expandable outcomes. Also provide run creation, state and history. Users can configure nested policies and scenarios without writing JSON files. Derive exact fields from `rescue/application/contracts/commands/`, `rescue/experiments/models/`, `rescue/mobilisation/models/` and `rescue/api/operations.py`; verify against actual API calls because the generated API schema does not describe all raw-request commands.

## Protocol and interaction

`POST /runs` creates a run. `POST /runs/{run_id}/operations/{operation}` accepts exactly a command object or the declared scalar arguments. `GET /runs/{run_id}/state` and `/history` read state and history. The codec defines decimal and nested encoding; preserve all response fields, including business rejections returned with HTTP 200. URL-encode run IDs. Configure exact allowed browser origin through `SPACE_RESCUE_ALLOWED_ORIGINS`.

Every primary control is keyboard operable and labelled, with visible focus and contextual feedback. Status must not rely on colour alone; respect reduced motion. Verify 360 and 1440 px widths. Comparison results must identify their scenario baseline and not imply they are live outcomes.
