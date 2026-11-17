# Implementation Plan: Composed Mission Simulations

**Branch**: planned `012-simulations`; actual checkout `main` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

## Summary

Build one HTTP-driven mission timeline from reusable situations. The all12 profile combines all situations; all11 removes concurrent submissions; all10 also removes duplicate delivery. A baseline uses full confirmation only. Each solver round calls mobilise, reads selected evaluations and submits their proposed requests through create_request. Events then change the same mission and trigger further solver rounds. Terminal output follows the complete execution, including post-completion deliveries.

## Technical Context

**Language/Version**: Python 3.14.10; uv 0.13.8.
**Primary Dependencies**: existing httpx==0.28.1; promote already locked pydantic==2.14.3 to a direct dependency for simulation contracts; existing server FastAPI==0.163.1 and uvicorn==0.38.0. No dependency upgrades.
**Storage**: server in-memory run; immutable local event heap and observations; no saved reports.
**Testing**: pytest==9.2.0, pytest-cov==7.1.0, coverage==7.17.3, ruff==0.17.5, import-linter==2.16.
**Target Platform**: local Windows/PowerShell and POSIX terminals.
**Project Type**: CLI package beside rescue, consuming its public HTTP interface.
**Performance Goals**: event-driven execution without real sleeps; at most 200 logical events and horizon 100 per built-in profile; no throughput benchmark.
**Constraints**: one mission per execution, lossless decimal times, no rescue imports from simulations, no new allocation logic, timeout-bounded HTTP with no automatic retries.
**Scale/Scope**: twelve reusable situations; four composed profiles; at most two concurrent HTTP submissions per scripted batch.

## Constitution Check

| Gate | Before research | After design |
|------|-----------------|--------------|
| Safe seat accounting | PASS: observe server totals; never invent allocations | PASS: check C>=0, P>=0, C+P<=D after events/batches; completion C=D |
| Final outcomes | PASS: exercise partial/refused/cancelled/expired requests | PASS: late messages cannot alter closed requests; snapshots distinguish audit changes from seat changes |
| Reliable operations | PASS: inject duplicate, delayed, reordered and competing submissions | PASS: bounded batches, unique identities, no mutation retries, explicit allowed winners |
| Simple design | PASS: separate HTTP simulation from rescue policy | PASS: four layers, shared runner, situation composition; no generic workflow language |
| Evidence and explainability | PASS: full original-problem timeline | PASS: declared evidence coverage plus live HTTP validation and existing suite |
| Spec/plan/tasks before code | PASS: this turn changes planning artifacts only | PASS: tasks are generated after this design; execution uses the bridge |

The prerequisite codec repair is transport-only and explicitly authorised by FR-012. No domain changes or constitution deviations are planned.

## Project Structure

### Documentation

spec.md, plan.md, [research.md](research.md), [data-model.md](data-model.md), [contracts/simulation.md](contracts/simulation.md), [contracts/timeline.md](contracts/timeline.md), [quickstart.md](quickstart.md), and [execution-handoff.md](execution-handoff.md). tasks.md is generated separately after Phase 1 using the same work packages.

### Source Code

```text
simulations/
  models/                  # strict immutable case/event/observation contracts
    api/                   # minimal typed request/response wire contracts
    vocabulary/            # operation, situation and event enums
  adapters/
    ports/mission_api.py    # MissionApiABC; imports only simulation models
    http/mission_api.py     # httpx translation, timeouts and bounded batch I/O
  services/
    run_scenario.py         # event loop and evidence checks
    solver_round.py         # mobilise proposal -> selected create_request calls
    scenarios/             # all_twelve.py, eleven.py, ten.py, baseline.py, catalogue.py
    situations/
      rescue/{completion,remobilisation}/
      requests/closure/
      communication/{delivery,ordering}/
      safety/{validation,finality,concurrency}/
      availability/{shortfall,updates}/
  entrypoints/              # cli.py, render.py, __main__ delegates here
tests/
  unit/simulations/{models,services,adapters,entrypoints}/
  integration/api/http/     # prerequisite codec regression
  integration/simulations/http/
  e2e/simulations/timeline/
  architecture/simulations/
```

**Structure Decision**: top-level simulations is an outer HTTP client, never a child of rescue and never a second business simulator. One class or situation per file; only create the files a task needs. Pure models import no adapters/services. Services receive MissionApiABC and an observation callback; concrete adapter construction and console writes belong to the CLI. Adapters import simulation models only. No raw dictionaries cross these internal boundaries; JSON mappings stay in the HTTP adapter.

## Global Constraints

- Spec 012 is authoritative. The twelve entries are situations inside one mission, not twelve scenario runs.
- All mission mutations and reads use spec 011 HTTP; no imports of rescue, direct store access or calls to the internal experiments simulator.
- mobilise returns a proposal and does not create requests. Consume value.evaluations with selected=true, in rank order; copy decision_id, ship_id, proposed_seats and revision.revision_id into create_request. Never assume a serialized selected property exists.
- Every real request allocation originates in a selected solver evaluation. The invalid-quantity action and competing duplicate proposal are explicit negative probes; label them as such.
- Preserve server reasons/statuses. HTTP 200 can contain a rejected business result. Expected rejections are evidence, not transport failures.
- Enforce at most 200 logical events, horizon 100, and two concurrent submissions. Drain declared post-completion events; never continue empty solver loops.
- HTTP phase timeouts: connect/pool 2 seconds, read/write 10 seconds; retries=0 and trust_env=False for this local client. Timeout after a mutation means outcome unknown; fail and do not resend.
- Exactly one parent-owned MissionApiABC and one function-scoped fake are shared across tests. No worker invents another interface or edits another worker's paths.
- Every module/class/public function explains What / When called / Why and references the feature design diagram. Keep one class per file, following P-0001/P-0002.
- Do not commit, push or open a PR. Implement from an isolated workspace through start-work and the Spec Kit bridge; planning in the current checkout does not authorise product edits on main.

## Execution Design

See the [timeline contract](contracts/timeline.md) for fixed ten-seat fixture and situation evidence. A heap ordered by (logical_time, phase, insertion_sequence) schedules explicit events. Request-triggered actions bind returned request IDs by ship and occurrence; no predicted IDs. Each solver round logs its proposal, submits selected requests, observes outcomes and schedules their scripted ship behavior. Recompute after all actions at a logical instant or a concurrent batch; do not allocate between members of a batch. A no-change shortfall waits for the next queued fleet/event update, not an immediate polling loop.

Completion suppresses further solver requests but does not terminate declared negative probes or late deliveries. End when events are exhausted or a bound fails. Compare declared/observed situation sets, final state and accounting checks. On failure keep the observed prefix, identify the failed event, continue other independent profiles for --all and return failure overall.

## Parallel Delivery

Use canonical tasks.md and [execution-handoff.md](execution-handoff.md). Freeze models/port before dispatch. Independent adapter, runner and situation work receives [P] markers and disjoint ownership. Scenario assembly waits for situation definitions; CLI waits for runner/adapter interfaces; parent alone edits shared configuration, package initializers and documentation index. Fresh implementer and task reviewer contexts; parent verifies evidence before checking tasks. Finish with one whole-change review. The [execution diagram](design-diagrams.md) is supplementary.

## Verification

First repair and verify valid nested API payloads and the proposal/create-request lifecycle. Test models without I/O; runner with the shared fake; HTTP translation using MockTransport; API integration via TestClient; whole-timeline smoke through an already-running loopback server. Mark real-server tests live_http; default gates select not live_http, while explicit live selection fails clearly without its server URL. No real server launch during this planning turn.

Extend Makefile lint/format, pytest coverage and architecture checks to simulations. Preserve every existing rescue coverage floor and add >=80% branch coverage per simulation layer. Configure import-linter root_packages for rescue and simulations, including forbidden simulations->rescue, pure models, adapter-inward and service/entrypoint contracts. Replace the existing architecture test's hard-coded contract count with assertions covering the declared required contracts. Full final gate: make install, make check-all, then documented all12/all11/all10/baseline live runs. Runtime results are not claimed by this plan.
