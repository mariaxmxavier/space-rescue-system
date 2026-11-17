# Implementation Plan: Mobilisation Conformance

**Branch**: `006-mobilisation-conformance` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/006-mobilisation-conformance/spec.md`

## Summary

Split `rescue/mobilisation/` into cosmic-python layers inside the component: one entity per file
in `models/`, five allocation algorithms in `algorithms/<name>/` behind one functional interface,
and the decision use case in `services/`. Each algorithm returns its allocation and a trace of the
steps it took. The decision service logs that trace, and the comparison entrypoint prints it.
Greedy earliest-arrival stays the default, so behaviour and demo output are unchanged.
Rationale: [research.md](research.md). ADR: [0001](../../docs/architecture/decisions/0001-mobilisation-algorithms.md).

## Technical Context

**Language/Version**: Python 3.14.10 (uv 0.13.8, pinned by 002)
**Primary Dependencies**: `ortools==9.15.6755` (new; pulls `numpy`, `pandas`, `protobuf`, `absl-py`, `immutabledict`, locked by `uv.lock`). Standard library `heapq`, `logging`, `enum`, `dataclasses`.
**Storage**: N/A (pure functions)
**Testing**: pytest 9.2.0, pytest-cov 7.1.0, import-linter 2.16 (all pinned by 002)
**Target Platform**: Windows / Linux / macOS developer machines and CI (`.github/workflows/check.yml`)
**Project Type**: library package plus a CLI entrypoint for the comparison
**Performance Goals**: each algorithm decides a 5-ship scenario in under 1 s; the comparison runs all scenarios in under 10 s
**Constraints**: no I/O or clock inside `rescue/mobilisation/` (contracts `domain-io` and the AST test in `tests/architecture/boundaries/`); demo output byte-identical
**Scale/Scope**: about 5–20 candidates per decision and demand up to about 100 seats

## Constitution Check

| Principle | Gate | Status |
|---|---|---|
| I Safe Seat Accounting | Allocations never exceed demand or allocatable seats; the decision service validates every algorithm's answer before recording it | Pass |
| II Final Request Outcomes | Mobilisation only proposes; reservation flow untouched | Pass |
| III Reliable Operations | No change to the application or adapters | Pass |
| IV Simple Design: explained strategy | ADR 0001 plus a README per algorithm; extra abstraction (the allocator interface) justified by five implementations | Pass |
| IV Simple Design: rules separate from infrastructure | OR-Tools is reached only from `algorithms/`; models and services import it never (new contract) | Pass |
| V Evidence | Shared contract tests run on all five algorithms; demo unchanged | Pass |
| Scope: fleet-wide optimisation excluded | Interface is per mission; min-cost flow is not used across missions | Pass |
| Dependencies exact | `ortools==9.15.6755` | Pass |

Post-design re-check: no change, all pass.

## Project Structure

### Documentation (this feature)

```text
specs/006-mobilisation-conformance/
├── spec.md  plan.md  research.md  data-model.md  quickstart.md
├── contracts/allocator.md        # the shared algorithm interface
├── contracts/import-contracts.md # new import-linter contracts
└── tasks.md                      # /speckit-tasks
```

### Source Code

```text
rescue/mobilisation/
├── __init__.py                   # docstring: why mobilisation exists
├── models/                       # entities, value objects, pure rules (no ortools)
│   ├── __init__.py               # re-exports, so `from rescue.mobilisation.models import X` keeps working
│   ├── algorithm_name.py         # AlgorithmName (StrEnum, closed set)
│   ├── policy.py                 # MobilisationPolicy         ← UML: MobilisationPolicy
│   ├── candidate.py              # Candidate, arrival_instant
│   ├── decision_context.py       # DecisionContext
│   ├── skip_reason.py            # SkipReason (StrEnum), static_skip_reason
│   ├── allocation.py             # Allocation, AllocationResult
│   ├── trace_step.py             # TraceStep
│   ├── offer_evaluation.py       # OfferEvaluation             ← UML: OfferEvaluation
│   └── decision.py               # MobilisationDecision        ← UML: MobilisationDecision
├── algorithms/                   # one folder per algorithm; imports models (+ ortools)
│   ├── __init__.py               # Allocator type + ALLOCATORS: AlgorithmName → Allocator
│   ├── greedy/        allocate.py  README.md  diagram.mmd   # earliest_arrival (default), largest_capacity
│   ├── priority_queue/ allocate.py README.md  diagram.mmd   # heapq
│   ├── min_cost_flow/ allocate.py  README.md  diagram.mmd   # ortools SimpleMinCostFlow
│   ├── cp_sat/        allocate.py  README.md  diagram.mmd   # ortools CP-SAT
│   └── knapsack/      allocate.py  README.md  diagram.mmd   # ortools KnapsackSolver
└── services/
    ├── decide.py                 # select_offers: validate → allocate → check → explain → log trace
    └── compare.py                # compare(scenarios, allocators, clock) → metrics rows (pure; clock injected)

benchmarks/mobilisation/compare.py  # entrypoint: real clock, logging config, prints table and trace
                                    # (outside rescue/: the architecture test forbids clocks there)

tests/unit/mobilisation/
├── models/test_<entity>.py       # one per model file
├── algorithms/test_allocator_contract.py   # parametrised over all five
├── algorithms/test_<name>.py     # per-algorithm behaviour and ties
└── services/test_decide.py  test_compare.py
tests/e2e/benchmarks/compare/test_compare_cli.py
tests/unit/mobilisation/policies/test_policies.py → moved to services/test_decide.py (imports updated)
```

Removed: `rescue/mobilisation/models.py`, `rescue/mobilisation/policies.py`.
Touched outside mobilisation (import path only): `rescue/application/central.py:51`.
Touched config: `pyproject.toml` (dependency and contracts), `uv.lock`, `Makefile` (`compare` target; lint covers `benchmarks`), Mobilisation class diagram (adds `AlgorithmName`).

**Structure Decision**: component-first cosmic layout inside the existing `mobilisation`
component (roadmap: conform in place). `algorithms/` plays the adapter role: it wraps the external
solver library and is injected into the service through the `Allocator` interface. It is named for
what it holds because the user asked for one folder per algorithm.

## Execution Trace (logs)

- Every algorithm returns `AllocationResult(allocations, trace)`. `trace` is a tuple of `TraceStep(algorithm, step, ship_id, detail)` covering: inputs considered, ordering or model built, each pick or skip, and solver status.
- `services/decide.py` logs each step through `logging.getLogger("rescue.mobilisation")` at DEBUG, with the step fields in `extra`. Logging lives in services, never in models (cosmic-python observability rule).
- `benchmarks/mobilisation/compare.py --trace` configures a JSON-lines handler, so the steps print as they run. Without `--trace` only the comparison table prints.

## Parallel Execution (multi-agent)

Phase order: Setup → Foundation (models, interface, decide service, contracts) → **five algorithm
folders in parallel [P]** → comparison → docs and diagrams [P] → polish. Each algorithm task owns only
its own folder and its own test file, so parallel writers never overlap (Constitution: development
workflow). Tasks with a shared file (`algorithms/__init__.py`, `pyproject.toml`) are serial.

## Complexity Tracking

| Addition | Why needed | Simpler alternative rejected because |
|---|---|---|
| `Allocator` interface plus registry | Five interchangeable algorithms, user requirement | One `if strategy ==` chain mixes the decision with every algorithm |
| OR-Tools runtime dependency | Min-cost flow, CP-SAT and knapsack solvers | Hand-written solvers are more code and less trustworthy |
| `benchmarks/` top-level folder | Run time needs a real clock, which the domain may not touch | Putting the clock in `rescue/mobilisation` breaks the 002 architecture test |
