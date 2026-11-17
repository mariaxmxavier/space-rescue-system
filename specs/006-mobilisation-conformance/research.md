# Research: Mobilisation Conformance

Algorithm survey and sources: [docs/reference/mobilisation-algorithms-research.md](../../docs/reference/mobilisation-algorithms-research.md).
This file records the implementation decisions.

## R1. Where the algorithms live

- **Decision**: `rescue/mobilisation/algorithms/<name>/`, importing `models/` only (plus `ortools`). The decision service receives an `Allocator` through a registry it can be given (`allocators=` parameter, defaulting to `ALLOCATORS`).
- **Rationale**: clean architecture keeps the solver a detail behind an interface, and cosmic-python puts external libraries in the adapter role and injects them into services. Folder per algorithm because the user asked for it.
- **Alternatives**: algorithms inside `models/` (rejected: drags `ortools` into the entities); a top-level `rescue/algorithms` package (rejected: roadmap says conform in place).

## R2. Interface shape

- **Decision**: a plain function type `Allocator = Callable[[tuple[Candidate, ...], int, Instant], AllocationResult]`. No ABC or Protocol class.
- **Rationale**: the algorithms are stateless; a function is the smallest shared interface and matches the project's functional style.
- **Alternatives**: `typing.Protocol` (an extra type for no gain); ABC (needs classes).

## R3. Keeping skip reasons identical

- **Decision**: the decision service computes reasons, not the algorithm.
  1. Static reasons from the candidate alone: `unavailable`, `quote_not_held`, `expired_quote`. These candidates are never offered seats.
  2. The algorithm returns **every** candidate in rank order, with seats (0 when it does not choose one).
  3. Walking that order with a running remaining demand, a zero-seat candidate gets `insufficient_demand`, then `exhausted`, then `quote_exceeds_remaining_demand`, then `insufficient_capacity` (today's precedence). Otherwise it gets the new `not_chosen`.
- **Rationale**: for greedy earliest arrival this replays today's loop exactly, so the demo is byte-identical. Other algorithms reuse the same explanation.
- **Check**: the service rejects (raises `DomainValidationError`) an allocation that over-allocates a ship, exceeds demand, splits a held quote, gives seats to a statically skipped ship, or does not list every candidate exactly once. That is the trust boundary between decision and algorithm.

## R4. Per-algorithm modelling

| Algorithm | Model | Held quotes (all-or-nothing) | Ties |
|---|---|---|---|
| greedy | sort all by key, take `min(allocatable, remaining)`; `earliest_arrival` key `(arrival, ship_id)`, `largest_capacity` key `(-allocatable, arrival, ship_id)` | taken whole when it fits, else skipped (today's rule) | ship id |
| priority_queue | `heapq.heapify` on `(arrival, ship_id)`; pop until demand met | same as greedy | ship id |
| min_cost_flow | source → ship (cap = allocatable) → sink (cost = arrival − decision time, seconds); `solve_max_flow_with_min_cost` with source supply = remaining demand | decided first, greedily by arrival (a flow cannot express all-or-nothing); README states the limit | ship id order of arc creation |
| cp_sat | `x_i ∈ [0, cap_i]`, `use_i ∈ {0,1}`, `x_i ≤ cap_i·use_i`, `x_i ≥ use_i`; quoted: `x_i = q_i·use_i`; `Σx ≤ D`. Solve 1: maximise `Σx`. Solve 2: fix `Σx`, minimise `T·(n+1) + Σuse` with `T ≥ arrival_i·use_i` | native | `num_workers=1`, `random_seed=0`, then output sorted by (arrival, ship_id) |
| knapsack | `KnapsackSolver` branch-and-bound; item = ship, weight = value = whole offer (quote seats or allocatable), capacity = D | native | solver order is input order sorted by (arrival, ship_id) |

Rank order for the non-greedy algorithms: chosen ships by (arrival, ship_id), then unchosen ships by the same key.

## R5. Trace and logging

- **Decision**: algorithms return `TraceStep`s as data; `services/decide.py` logs them at DEBUG via `logging.getLogger("rescue.mobilisation")`. The entrypoint attaches a JSON-lines handler when `--trace` is set.
- **Rationale**: domain code stays free of I/O (contract `domain-io`, AST test), but every step stays observable. Logging lives in services (cosmic-python).
- **Alternatives**: `print` inside algorithms (breaks purity, untestable); returning only the final allocation (does not meet the user's need to see each step).

## R6. Measuring run time

- **Decision**: `services/compare.py` takes `clock: Callable[[], float]`. `benchmarks/mobilisation/compare.py` passes `time.perf_counter`. Tests pass a fake clock.
- **Rationale**: the AST test in `tests/architecture/boundaries` forbids `perf_counter` calls inside `rescue/mobilisation`. Injecting the clock keeps the logic testable at 100% coverage.

## R7. OR-Tools version and APIs

- `ortools==9.15.6755` is the latest release and ships `cp314` wheels.
- APIs: `ortools.graph.python.min_cost_flow.SimpleMinCostFlow`, `ortools.sat.python.cp_model.CpModel` / `CpSolver`, `ortools.algorithms.python.knapsack_solver.KnapsackSolver`. Each is verified in the setup task with a smoke import before any algorithm task starts.
- `.python-version` pins `3.14.10+gil`. uv 0.13.8 can select a free-threaded 3.14 interpreter when it appears first on `PATH`; OR-Tools 9.15.6755 publishes the Windows CPython 3.14 wheel for the GIL-enabled ABI. The local free-threaded environment had no compatible Windows wheel, while a fresh GIL-enabled project environment installed and imported all three APIs. Sources: [uv Python variants](https://docs.astral.sh/uv/concepts/python-versions/) and [OR-Tools 9.15.6755 release files](https://pypi.org/project/ortools/9.15.6755/).

## R8. Closed algorithm vocabulary

- **Decision**: `AlgorithmName(StrEnum)`: `earliest_arrival`, `largest_capacity`, `priority_queue`, `min_cost_flow`, `cp_sat`, `knapsack`. `MobilisationPolicy.selection_criteria` still accepts a string or key/value pairs, as in the UML, but the resolved strategy must be an `AlgorithmName`; otherwise construction fails.
- `SkipReason(StrEnum)` keeps today's string values, so equality with the old strings and the printed output are unchanged.
