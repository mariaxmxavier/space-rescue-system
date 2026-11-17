# Frontend Module Interfaces

This contract freezes integration seams before capability work. Modules depend on `shared`, never on each other. The shell owns composition and all feature modules export one `register<Capability>(context)` function from their `index.js`. Modules do not import API or mutate the run snapshot directly.

## Shared interfaces

```js
api.createRun({ application_run_id, central_id, policies, scenarios })
api.invoke(runId, operationName, payload)
api.readState(runId)
api.readHistory(runId)

workspace.getSnapshot() // { runId, snapshot, refreshedAt, stale }
workspace.subscribe(listener) // unsubscribe function
workspace.selectRun(runId)
workspace.createRun(input)
workspace.refreshState()
workspace.loadHistory() // explicit action only
workspace.invoke(operationName, payload) // captures selected runId at submission

registerCapability({ root, api, workspace, forms, outcomes })
forms.commandForm({ operation, schema, onSubmit })
forms.scalarForm({ operation, fields, onSubmit })
outcomes.render(result, { operation, label })
```

`api.invoke` takes the run ID separately from the exact operation body. It returns the decoded complete response and throws a transport error for unavailable or malformed transport. Application-level rejection remains a normal response for the feature to display. It never retries mutation calls.

The workspace uses request generations and captured run identity so an old refresh or command cannot update a newly selected run. After an operation completes it refreshes committed state. A failed refresh preserves prior state and marks it stale. History is loaded only from an explicit user action.

## Capability ownership

| Module entry | Owns use cases | Paths owned |
| --- | --- | --- |
| `missions/index.js` | mission registration, progress, mission history | `web/missions/**` |
| `fleet/index.js` | ship registration, availability, offers, fleet inspection | `web/fleet/**` |
| `quotes/index.js` | RFQ, quote recording and quote lifecycle | `web/quotes/**` |
| `requests/index.js` | direct request creation, cancellation and expiry | `web/requests/**` |
| `mobilisation/index.js` | mobilisation actions, decisions and traces | `web/mobilisation/**` |
| `communication/index.js` | response input, deliveries, sessions, synchronisation and recovery | `web/communication/**` |
| `experiments/index.js` | run scenario/policy configuration and comparison inspection | `web/experiments/**` |
| shell | run creation/selection, tabs, common refresh and capability registration | `web/index.html`, `web/shell/**` |
| shared | HTTP codec, workspace state, generic form primitives and result rendering | `web/shared/**` |

If an operation is naturally cross-listed above, it has one primary owner: response entry belongs to communication; quote-to-request conversion belongs to quotes; mission request history is presented by missions, but request mutation actions are owned by requests.

## Cross-cutting rules

- Do not add business policy, seat totals, enum interpretations or simulated allocation logic to client modules. Render authoritative server data.
- Forms preserve input on rejection, distinguish omitted optional fields from zero/empty values, and construct the exact request shapes in [operation fields](operation-fields.md).
- All capability modules may read the shared workspace snapshot and call injected APIs. They may not create private run stores or use globals.
- To prevent integration collisions, only the shell owner edits `web/shell/app.js`; capability modules use their own `index.js` exports and the shell registers them during serial integration.
