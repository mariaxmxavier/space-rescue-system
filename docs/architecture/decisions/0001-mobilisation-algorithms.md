# ADR 0001: Mobilisation algorithms

- Status: Proposed
- Date: 2026-11-17
- Spec: [006 Mobilisation conformance](../../../specs/006-mobilisation-conformance/spec.md)
- Research: [Algorithms for mobilisation](../../reference/mobilisation-algorithms-research.md)

## Context

Mobilisation decides which ships to ask for seats, and how many from each. Until now one
function both chose the ships and recorded the decision, and the strategy was a free string with
two greedy orderings. Constitution IV requires an *explained* strategy. Nobody could say how good
the current rule is, because there was nothing to compare it with.

## Decision

1. **Separate the decision from the algorithm.** The decision step validates input, calls the
   policy's algorithm, and records each ship as selected or skipped with a reason. Every algorithm
   implements one interface: given candidates, unmet demand and the decision time, return seats
   per ship.
2. **Implement five algorithm families, one folder each**, all behind that interface. The greedy
   folder holds two strategies, so the registry has six entries.

| Algorithm | Why it is here | Trade-off | Time as implemented |
|---|---|---|---|
| Greedy, earliest arrival (**default**) and largest capacity (legacy) | Simplest rule; today's behaviour, reproduced exactly | Never revisits a choice; ignores side constraints | O(n log n): one sort, O(1) per ship |
| Priority queue (min-heap) | Same answer as greedy on the same snapshot | The heap is rebuilt on every call, so it gives no advantage for incremental updates; this family does not keep state | O(n) heapify, O(log n) per pop, O(n log n) per call |
| Minimum-cost flow (OR-Tools `SimpleMinCostFlow`) | Standard model for moving units from suppliers to demand; extends to several missions | Held quotes are preallocated greedily, not optimised with the flow; needs a cost model | One solver call on a network of n + 2 nodes and 2n arcs; no tight worst-case bound claimed |
| CP-SAT (OR-Tools `CpSolver`) | Takes side rules: whole-ship quotes, a staged objective, deterministic ship-id ties | Slowest family; the staged solve costs n + 2 solves per decision | No polynomial worst case; measured sub-second at scenario size |
| 0/1 knapsack (OR-Tools `KnapsackSolver`, branch and bound) | Correct model when an offer cannot be split | Whole offers only, so it can under-cover demand; the reported shortfall is the point of the comparison | Exponential in the number of ships in the worst case; the O(n·D) dynamic-programming bound does not apply to this implementation |

3. **Keep greedy earliest-arrival as the default**, so the demo and existing tests are unchanged.
   The `largest_capacity` ordering stays available through the registry and is not a default
   comparison row.
4. **Use OR-Tools `ortools==9.15.6755`** for min-cost flow, CP-SAT and the knapsack solver instead
   of writing solvers. Its solver code does no I/O, so the domain rules still hold.
5. **Rejected**: genetic algorithms and particle swarm. They only pay off on instances far larger
   than the mobilisation scenarios.

## Measured

The five-ship comparison scenarios (`make compare`, Windows 11, Python 3.14.10) gave these slowest
samples per algorithm: earliest arrival 0.16 ms, priority queue 0.17 ms, min-cost flow 0.31 ms,
CP-SAT 12.7 ms and knapsack 0.18 ms. The whole comparison ran in 0.88 to 1.05 s. The record is in the
US3 section of the [quickstart](../../../specs/006-mobilisation-conformance/quickstart.md).

## Consequences

- A comparison reports last-seat arrival, ships used, unused seats and run time per algorithm on
  shared scenarios. The known limits of each family are in its README under
  `rescue/mobilisation/algorithms/`.
- The project gains its first runtime dependency: `ortools==9.15.6755` and the packages it pulls in,
  all pinned in `uv.lock`.
- Adding an algorithm means adding one folder and one name to the closed set; the decision step does
  not change.
- Allocating across several missions at once stays out of scope; the constitution excludes
  fleet-wide optimisation.
