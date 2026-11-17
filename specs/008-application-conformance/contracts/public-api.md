# Contract: Public API Kept Stable

The refactor must not change anything a caller can observe (FR-008). The existing integration
suites and the demo byte compare check it.

## RescueCentral operations (same names, parameters, return types and results)

`register_mission`, `register_ship`, `publish_availability`, `publish_offer`, `request_quotes`,
`record_quote`, `accept_quote`, `create_request`, `reject_quote`, `expire_quotes`,
`cancel_request`, `expire_request`, `record_response`, `get_progress`, `get_history`,
`get_decision`, `get_deliveries`, `compare`, `mobilise`.

For every operation, the following stay the same: the `Result.status`, `Result.reason` and
`Result.value` returned for the same input and state; whether state is published; the order of IDs
drawn from `IdSource`, which the demo output depends on; and replay semantics.

## Import paths that must keep resolving

| Import | Used by |
|---|---|
| `from rescue.application.contracts import <any former name>` | `demo.py`, `experiments/runner.py`, 6 integration test modules |
| `from rescue.application import contracts` then `contracts.<name>` | `tests/unit/application/contracts/test_contracts.py` |
| `from rescue.application.central import RescueCentral` | `bootstrap.py` |
| `from rescue.bootstrap import new_run, RunContext` | callers, unchanged |

## Paths that change (callers updated in the same task)

| Old | New |
|---|---|
| `rescue.application.state.RunState` | `rescue.state.RunState` |
| `RescueCentral(application_run_id, central_id, store, clock, id_source)` | adds `simulator=` (only `bootstrap` builds it) |
| `rescue.experiments.models._frozen_tree` (private) | `rescue.values.is_deeply_immutable` |
