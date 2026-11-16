<!--
Sync Impact Report
Version: 2.0.0 -> 2.0.1 (terminology clarification only).
Modified principles: I. Safe Seat Accounting; IV. Simple Design;
V. Evidence and Explainability (vessel terminology replaced with ship).
Added sections: None.
Removed sections: None.
Dependent artifact updated: docs/reference/glossary.md uses Ship offer and ship.
Follow-up TODOs: None.
Review scratch material: remove this report before committing.
-->
# Space Rescue System Constitution

## Core Principles

### I. Safe Seat Accounting

- Missions MUST identify the station and a positive integer number of people to rescue.
  Ship offers MUST identify the ship, offered capacity, and estimated arrival time.
  Quantities and estimates MUST be valid for their context.
- For demand `D`, confirmed seats `C`, and pending seats `P`, operations MUST preserve
  `C >= 0`, `P >= 0`, and `C + P <= D`, and respect offered ship capacity.
- A mission MUST be complete only when `C = D`. Pending seats MUST NOT count as guaranteed transport.
- Status MUST show what is confirmed, what awaits responses, whether more help is needed,
  and the outcomes of individual requests.

### II. Final Request Outcomes

- Pending requests MUST support full acceptance, partial acceptance, refusal, cancellation,
  and expiration. Confirmations MUST NOT exceed the requested quantity.
- Partial acceptance MUST close the request and release the unconfirmed remainder.
  Refusal, cancellation, and expiration MUST release all seats pending on that request.
- Only pending requests MAY be cancelled or expired. Closed outcomes MUST remain unchanged,
  and confirmed seats MUST be counted exactly once.
- The system MUST allow further mobilisation whenever confirmed and pending seats leave unmet demand.

### III. Reliable Operations

- Repeated, delayed, or out-of-order messages and simultaneous operations MUST NOT distort
  mission accounting or alter closed decisions.
- Invalid operations MUST preserve previously accepted data.
- The solution MUST explain or implement how concurrent requests and responses preserve
  these commitments. Concrete mechanisms and message-handling policies belong in the plan
  and README.

### IV. Simple Design

- The design MUST keep rescue rules separate from storage, presentation, and transport.
  Additional abstractions and infrastructure MUST have a documented need.
- The system MUST select ships and request quantities using an explained strategy that
  considers offered capacity, arrival estimates, and mission rules.
- The README MUST explain strategy assumptions and how availability changes are handled
  without invalidating settled request outcomes.

### V. Evidence and Explainability

- Automated tests MUST verify seat accounting, request outcomes, invalid operations,
  insufficient capacity, and repeated, delayed, or out-of-order communication.
  Any implemented concurrency mechanism MUST also be tested.
- A reproducible demonstration MUST involve multiple ships, partial acceptance, refusal,
  further mobilisation, and completion through confirmed seats only.
- The README MUST explain how to run the demonstration and tests, design decisions,
  assumptions, and the approach to concurrent operations.

## Scope and Project Choices

- The [original problem](../../docs/context/original-problem.md) defines the required scope:
  reservation confirmation. Flights, boarding, routes, storm simulation, and global fleet
  allocation across missions are excluded.
- Python is the project's chosen language; the original problem permits other languages.
  Dependencies MUST use exact versions.
- In-memory persistence, direct method calls, and simulated cancellation and expiration
  are sufficient. A GUI, HTTP API, messaging service, external integration, and real timers
  are optional.
- Extras MUST have explicit requirements and preserve the core commitments.
- Terms are defined in the [project glossary](../../docs/reference/glossary.md).

## Development Workflow

- Specifications, plans, and executable tasks MUST precede implementation and trace to the
  original problem and this constitution.
- Input encodings, message identities, selection tie-breakers, and consistency mechanisms
  MUST be defined in specifications or plans when relevant, without prescribing class names
  or fixed task groups in this constitution.
- Tasks MUST identify their scope, dependencies, acceptance criteria, and verification.
  Parallel writers MUST have non-overlapping file ownership.
- Completion MUST record relevant check results. The delivered solution MUST pass its full
  test suite and run the documented demonstration.

## Governance

Plans and reviews MUST check compliance with this constitution and repository instructions.
Conflicts with the original problem MUST be raised explicitly. Assumptions MUST be recorded
in the README without weakening the rescue commitments. Deviations MUST document their
rationale and verification impact and receive maintainer approval before implementation.

Amendments MUST receive maintainer approval, record their impact on dependent artifacts,
and update the version and amendment date. Review affected specifications, plans, tasks,
and code. Use MAJOR for incompatible rule changes, MINOR for new or expanded rules, and
PATCH for wording-only changes. Preserve the original ratification date.

**Version**: 2.0.1 | **Ratified**: 2026-11-16 | **Last Amended**: 2026-11-16
