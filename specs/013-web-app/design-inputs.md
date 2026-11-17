# Web app design inputs

These are requested constraints and verified discovery notes for the design discussion, not an approved design or implementation plan.

## Requested constraints

- Apply [UI/UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/main/.claude/skills/ui-ux-pro-max/SKILL.md). CLI 2.15.0 was installed globally and initialised for Codex on 2026-11-17. The design-system queries `rescue operations dashboard` and `emergency operations dashboard` returned marketing landing-page patterns, which do not fit this operational tool. Treat them as unsuitable; use the skill's general accessibility guidance as a fallback and refine the visual design before creating screens.
- Use Clean Architecture and Cosmic Python: presentation and transport remain outer details, existing Python use cases retain business decisions, and dependencies follow the repository's current enforced boundaries.
- Organise by capability and use case in folders and subfolders. Interpret the user's word “cases” as use cases, including corresponding test groups. Confirm this interpretation during design; exact paths belong in the plan.
- Preserve the existing domain-first package layout. This feature does not authorise a general Python restructuring.
- Roadmap scope is HTML, CSS and JavaScript over the 011 HTTP API. No frontend framework has been selected.
- The user chose to proceed directly to Spec Kit planning without visual mockups. No design document was approved. Do not commit without explicit authorisation.

## Existing capability inventory

Source: `rescue/api/operations.py`, inspected 2026-11-17.

| Capability | Existing operations |
| --- | --- |
| Missions | `register_mission`, `get_progress`, `get_history` |
| Fleet and offers | `register_ship`, `publish_availability`, `publish_offer` |
| Quotes | `request_quotes`, `record_quote`, `accept_quote`, `reject_quote`, `expire_quotes` |
| Seat requests | `create_request`, `cancel_request`, `expire_request` |
| Communication | `record_response`, `get_deliveries`, `get_session`, `synchronise_inbound`, `recover_reports` |
| Mobilisation | `mobilise`, `get_decision` |
| Experiments | `compare` |

Additional API actions: create a run with policies/scenarios, read committed state, read complete call history. There is no run-list endpoint; reopening a known run must not assume one exists.

The API encodes inputs and results through `rescue/api/codec.py`; precise form contracts must be derived from command models and scalar argument descriptors during planning. The operation allowlist is not a substitute for inspecting those contracts.

## Access and refresh constraints

- Local access, without accounts, follows spec 011.
- Browser mutation origins must match configured allowed origins; serving arrangements and origin configuration must be designed together.
- State and history are separate reads. History reads retain complete earlier history responses, so do not poll history automatically.
- No product dependencies, code or server processes have been introduced during specification.

## Source material

- [Original problem](../../docs/context/original-problem.md)
- [Constitution](../../.specify/memory/constitution.md)
- [Roadmap](../../docs/planning/roadmap.md)
- [HTTP API specification](../011-http-api/spec.md)
- [Feature specification](spec.md)
