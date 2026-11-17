# Scripted rescue simulations design

**Superseded by the maintainer's composed-timeline correction and the canonical [012 plan](../../../specs/012-simulations/plan.md).** The twelve entries below are now reusable situations within one mission, not independent simulation runs. The plan, contracts and tasks own implementation; this initial brainstorming draft is historical context.

## Intent and scope

Demonstrate the [original problem](../../context/original-problem.md) through the spec 011 HTTP interface. Keep cases small, named and grouped by situation. The [specification](../../../specs/012-simulations/spec.md) owns acceptance criteria and the case catalogue.

## Approaches

- **Terminal walkthrough and final summary (selected by the maintainer):** show each action and mission progress as the case runs. Small and easy to follow.
- **Walkthrough plus saved reports:** supports later comparison but adds file output and configuration. Deferred.

## Behavior

List cases, run one or run all. Each execution creates an isolated run and uses returned identifiers for subsequent steps. Show every request's ID, ship and quantity, each response or closure and its reason, and progress after each action. End with case pass/fail, mission complete/incomplete, confirmed seats, pending seats and remaining unconfirmed seats. An expected incomplete mission can pass.

Use explicit scripted event times without sleeps. Submit simultaneous operations as a bounded batch; show identifiers and server-observed outcomes without claiming a fixed winner. Check accounting and allowed results after the batch. Failed expectations identify the step and observed difference. Independent cases continue after a case fails; any failure produces a failing overall exit status.

## Boundaries and folders

Proposed layout, applying Clean Architecture and Cosmic Python without changing rescue packages:

```text
simulations/
  models/                  # case, step and result contracts
  adapters/
    ports/                 # injected interface used by the runner
    http/                  # JSON and HTTP translation
  services/
    run_case.py             # shared execution and expectation checks
    cases/
      rescue/
      requests/
      communication/
      safety/
      availability/
  entrypoints/              # arguments, wiring, terminal rendering and exit status
```

One case per file; one class per file where needed. Models are pure; services receive the HTTP adapter through its interface. The entrypoint constructs the adapter and runner. The adapter translates the wire format into simulation contracts. No imports of rescue internals or bootstrap shortcuts; rescue code does not import simulations. Expectations observe rules rather than reimplementing ship selection.

The plan must extend packaging and quality gates to include simulations, preserve import contracts, and place checks under tests/<type>/simulations/<topic>/. Every module, class and public function follows the repository's explanatory docstring rule.

## Constraints and exclusions

Reuse pinned project dependencies where sufficient. The user starts the local server; simulations accept its address. No automatic server startup, saved reports, GUI, performance framework, real timers, flights or new rescue behavior. The design fails its purpose if it hides requests or bypasses HTTP to access application state.

## Calls left to planning

The internal layout is the author's recommendation. Planning selects exact fixtures, operation sequences, payload contracts, command spelling, failure bounds and focused tests. It must confirm every case is expressible through the current API and surface gaps rather than bypassing HTTP.

The [flow diagram](2026-11-17-rescue-simulations-design-diagram.md) is supplementary.

**Status**: Short design awaiting maintainer approval; implementation has not started.
