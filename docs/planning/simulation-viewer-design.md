# Simulation viewer design

## Intent

Let a visitor understand Space Rescue by selecting a case, without creating a run, configuring identifiers or submitting operations. The user explicitly chose to start paused at the beginning. Playback and arbitrary timeline selection must show the same simulated system state in every panel.

The web app MUST also implement and display everything required by [spec 013](../../specs/013-web-app/spec.md) and its [UI contract](../../specs/013-web-app/contracts/ui.md), [operation fields](../../specs/013-web-app/contracts/operation-fields.md) and [frontend module interfaces](../../specs/013-web-app/contracts/frontend-modules.md). The case viewer is an additional entry point; full browser capability coverage remains mandatory.

## Full spec 013 coverage

- Preserve all five user journeys: rescue coordination, run and outcome inspection, quotes and shared capacity, communication and recovery, and strategy/scenario comparison.
- Provide discoverable labelled browser actions and complete outcome inspection for all 22 inventoried public operations, plus run creation, reopening/switching, state refresh and explicit call-history loading. Selecting a simulation case must not require these manual steps, but their controls must remain reachable.
- Show all available committed data and returned fields, including mission progress and history, fleet availability and offer revisions, RFQs, quotes and holds, requests, allocations, candidate evaluations, reasons and traces, messages, deliveries, sessions, recovery reports, experiment configurations, results and timelines. Use readable summaries with expandable complete records.
- Distinguish demand, confirmed seats, pending seats, unmet demand and temporary holds. Keep mission history separate from ordered call history with submitted input and complete results.
- Preserve the shared selected live run across Operations and Exploration. Clearly label historical simulation snapshots and configured comparison baselines so neither is confused with current live state.
- Meet FR-001 through FR-016, all listed edge cases and SC-001 through SC-006, including keyboard access, 360–1440px layouts, loading/empty/rejected/unavailable/stale states, preserved input, protected operation identity, no automatic mutation retries and stale-response isolation.
- Document local launch, connection, the demonstration, advanced workflows and in-memory run loss after server restart.

Each case displays the records and events actually produced by its execution. A case that does not exercise quotes, recovery or comparisons must show an explicit empty or not-exercised state; do not fabricate those outcomes. Those capabilities remain fully usable and inspectable through their spec 013 workflows.

## Existing constraints

The vanilla HTML/CSS/JavaScript web app calls the FastAPI operation API. Spec 012 defines four composed simulation profiles: baseline, all10, all11 and all12. Its models, situations and runner exist, but the HTTP adapter and profile catalogue are absent; runner calls also differ from the current port signatures. The runner currently discards its observations. Integration therefore includes completing the necessary simulation execution path, rather than adding illustrative browser fixtures.

Keep rescue domain policies unchanged. Operations use the public HTTP API, including solver-selected allocations, final request outcomes and communication sequencing. Keep simulation services independent of rescue imports. Preserve import contracts, coverage floors, docstrings and one class per file. No commits, pushes or pull requests.

## Approach

Use actual simulation execution with a retained transcript and state snapshots. A case selection creates a fresh execution; after preparation the viewer is paused at logical time zero. Playback presents this authoritative recording. This lets users jump both forward and backward immediately without replaying mutations or changing the simulation result.

Executing mutations only as playback advances would prevent immediate forward seeking and make seeking backward require extra runs. Browser-authored simulated states would duplicate business rules. Neither meets the requirement as well as a recorded real execution.

Builder choice: provide the catalogue and execution through an outer HTTP entrypoint, keeping transport composition outside the simulation services and the rescue domain. Use the existing Python and browser stack. Do not introduce a frontend framework or hosting service.

## Viewer

- Default entry: a clearly labelled case selector with human-readable summaries and situation counts. Include all four spec 012 profiles; choose the baseline initially, paused.
- Selecting a case prepares a fresh run automatically. Display preparation progress or a specific recoverable error. Never silently substitute fabricated data or mark a failed case as successful.
- Display mission demand, confirmed, pending, outstanding seats and mission status; ship availability and commitments; requests and their outcomes; solver proposals versus submitted requests; communication events and evidence.
- Keep a shared logical-time cursor. Provide play/pause, replay, previous/next event, speed, a labelled native range control and editable time selection. Keyboard users can select any time without dragging. At times between events show the last committed snapshot and make that timing explicit.
- Preserve deterministic ordering for events at equal logical times. Let the event list select each individual event even when their times match. Process post-completion events rather than stopping at mission completion.
- All panels derive from the selected snapshot. Show future events as upcoming without leaking future outcomes into the selected state. Clearly separate mission completion from case evidence pass/fail.
- Switching cases stops previous playback and ignores stale responses. Controls remain responsive; errors offer retry. Respect reduced motion by retaining paused initial presentation and avoiding decorative movement.
- Keep the existing manual operations workspace available under an advanced disclosure. It observes the live run, with a clear distinction from the historical viewer cursor.

## Visual direction

Extend the existing high-contrast slate, white and navy console described in spec 013. Use semantic tokens, system fonts and tabular numerals. Place the case selector first, mission and fleet views next, and the timeline alongside the event explanation. Reflow to one column on narrow screens; preserve readable labels, visible focus, 44px controls and textual status indicators.

UI/UX Pro Max's design-system search returned a generic landing-page pattern, which does not fit this viewer. Two targeted product searches produced no verified match. Retain the repository's established dashboard direction instead. Its focused dragging-movements guidance supports native keyboard-operated timeline input plus event navigation buttons.

## Verification

Test real simulation profiles through the API, including solver-driven request creation, evidence, final progress and retained snapshots. Test playback state transitions, between-event seeking, equal-time ordering, case switching and stale replies. Browser checks cover case selection, paused initial state, play/pause, seeking backward and forward, keyboard controls, responsive layout and preparation failure recovery. Run the pinned-toolchain install and repository check gates; report any baseline failures separately and fix regressions introduced here.

Maintain an explicit coverage checklist against spec 013's FR-001–FR-016, five user journeys and SC-001–SC-006. Verify input and complete outcome inspection for every public operation and run/state/history endpoint. Simulation playback checks supplement these acceptance checks; they do not replace them.

## Scope limits and builder decisions

This is a local simulation viewer and the full spec 013 browser app, not a multi-user durable run service. Keep execution bounded by the existing event/time limits. Prefer a single prepared transcript response unless measured execution time requires incremental delivery. Exact endpoint paths, component boundaries and display wording belong to implementation planning. Extend simulation/API transport as needed for these viewer behaviors and complete any missing spec 013 capabilities; do not broaden into unrelated application changes.
