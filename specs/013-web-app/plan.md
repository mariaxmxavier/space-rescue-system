# Implementation Plan: Rescue Web App

**Branch**: `main` (actual; `013-web-app` proposed) | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

## Summary

Build a local browser app with Operations and Exploration tabs sharing one selected run. Provide guided access to all 22 existing operations and complete outcomes. Label comparison results as simulations of configured scenario baselines. Group modules by capability and use case; business decisions remain in the existing API and services.

User-approved extension: implement the [connected simulation viewer](../../docs/planning/simulation-viewer-design.md) as the default entry point, preserving all capabilities above under the advanced workspace. Complete missing spec 012 execution prerequisites, expose catalogue/execution over HTTP and retain authoritative state frames. Keep the existing vanilla browser/Python stack. Selecting a case starts paused; a single cursor synchronizes all records with arbitrary forward/backward seeking. Work in the existing checkout so the user's uncommitted approved design and all parallel changes remain reviewable together; no commits, pushes or PRs.

Parallel implementation ownership: simulation worker owns `simulations/**` and its tests; viewer worker owns `web/simulations/**` and browser simulation tests; capability worker owns other feature/shared browser modules and their tests; parent owns API transport/endpoints, shell composition, shared browser fixtures, configuration, documentation and final integration. The execution adapter is disposable under `/tmp`, derived from canonical task IDs.

## Technical Context

- Browser HTML, CSS and JavaScript ES modules; existing Python 3.14.10, FastAPI 0.163.1 and uvicorn 0.38.0. No frontend framework.
- Run data remains in memory; known run IDs can be reopened. No run-list endpoint exists.
- Add browser-driven Playwright Python tests, with exact dependency versions pinned at implementation time and matching managed Chromium; retain `make check-all`.
- Target local modern browsers at widths 360–1440 px. No accounts or remote hosting.
- Preserve existing domain rules, origin restrictions and command identities; never automatically retry uncertain mutations. Load history only on demand due to nested response growth.

## Constitution Check

| Principle | Before research | After design |
| --- | --- | --- |
| Safe seat accounting | Pass: API authoritative | Pass: distinguish confirmed, pending and held seats; test shared capacity |
| Final outcomes | Pass: use existing operations | Pass: test partial acceptance, refusal, cancellation, expiry and late responses |
| Reliable operations | Pass: no changed business rules | Pass: test duplication, recovery, stale responses and uncertain calls |
| Simple design | Pass: browser is an outer adapter | Pass: capability modules and existing service boundaries |
| Evidence | Pass: retain existing checks | Pass subject to browser journeys and demonstration |

## Project Structure

```text
specs/013-web-app/       # plan, research, model, contracts, quickstart; tasks later
web/
  index.html
  shell/                 # tabs, navigation, run selection
  shared/                # API client, state coordination, common UI
  missions/              # registration, progress, history
  fleet/                 # ships, availability, offers
  quotes/                # quotes lifecycle
  requests/              # seat requests and outcomes
  mobilisation/          # decisions and trace
  communication/         # deliveries, sessions, recovery
  experiments/           # configuration, comparison
tests/e2e/web/           # browser journeys grouped by capability
```

Nested folders separate use cases where useful. Existing Python packages stay in place. The static frontend can be served locally with `python -m http.server`; API origin configuration must explicitly allow the frontend origin.

## Parallel Execution

`[P]` marks independent work after prerequisites. `$speckit-tasks` will provide task IDs, acceptance criteria and exact non-overlapping file ownership.

1. Inventory actual command and nested model fields and freeze shared client, state, event and UI composition contracts. Establish browser runner and fixtures.
2. [P] Shell, navigation, API and run state (`web/index.html`, `web/shell`, `web/shared`).
3. [P] Missions, seat requests and mobilisation (`web/missions`, `web/requests`, `web/mobilisation`).
4. [P] Fleet, offers and quotes (`web/fleet`, `web/quotes`).
5. [P] Communication and experiments (`web/communication`, `web/experiments`).
6. [P] Browser tests and documentation, with exclusive ownership of `tests/e2e/web` and assigned docs; coordinate selectors and fixtures against frozen interfaces.
7. Integrate centrally and verify all operations, browser journeys, accessibility, architecture and the existing suite. No writers overlap paths.

See [research](research.md), [data model](data-model.md), [UI contract](contracts/ui.md), [quickstart](quickstart.md), and [design inputs](design-inputs.md). UI/UX Pro Max was queried; its marketing patterns did not fit, so visual design still needs refinement. No tasks file is generated in this planning phase.
