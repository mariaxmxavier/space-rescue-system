# Research: Algorithms for Mobilisation

Date: 2026-11-17. Feeds [ADR 0001](../architecture/decisions/0001-mobilisation-algorithms.md).

## The problem in one line

One mission needs `D` seats. `n` ships each offer `c_i` free seats and arrive at `t_i`. Some ships
hold a quote that must be taken whole. Choose how many seats `x_i` to request from each ship so
that `Σ x_i ≤ D`, `0 ≤ x_i ≤ c_i`, and the people are covered as early as possible.

In the literature this is **vehicle or supplier selection under a demand constraint**. Its
whole-ship variant is the **covering (min-)knapsack** problem.

## What the literature uses

| Family | Where it shows up | Finding |
|---|---|---|
| Greedy priority rules | Bus evacuation, ambulance dispatch | Fast and good enough when conditions change quickly; exact models are often too slow in an emergency [1][2] |
| Priority queues | Dispatch systems where availability changes | Same choice as greedy; insertion and removal in O(log n) instead of sorting again [3] |
| Network flow (min-cost flow) | Allocating resources from many suppliers to many sinks | Optimal and polynomial; natural when several missions share ships [4] |
| Integer and constraint programming (MILP, CP-SAT) | Evacuation planning with deadlines, costs, ship limits | Optimal under arbitrary side constraints; run time grows with model size [1][5][6] |
| Knapsack / covering knapsack | Supplier selection with indivisible orders | Exact by dynamic programming in pseudo-polynomial time O(n·D) [7][8]. This project implements branch and bound instead; see the knapsack README |
| Metaheuristics (GA, PSO) | Large vehicle-assignment instances | Only pays off at scales far beyond ours [9] |

## Takeaways for this project

- Our instances are small (a handful of ships, tens of seats), so every exact method is fast enough. The comparison is about quality and explainability, not feasibility.
- When seats can be requested one by one, greedy by earliest arrival is already optimal for "earliest last arrival". The exact methods earn their place once constraints are added (deadlines, a maximum number of ships, whole-ship quotes).
- Knapsack fits only the all-or-nothing case. It is kept as the contrast that shows what is lost when offers cannot be split.
- Metaheuristics are left out: our problem sizes are too small for them to pay off.

## Implementation check

The working implementations, and what was measured on them, are recorded in each algorithm's README
and in the US3 section of the [quickstart](../../specs/006-mobilisation-conformance/quickstart.md).
The literature bounds above are for the textbook methods. They are not the implemented bounds:

- Priority queue: the implementation rebuilds the heap per call (O(n log n)), not incremental updates.
- Minimum-cost flow: OR-Tools `SimpleMinCostFlow`, a network-simplex solver, one call per decision.
- Knapsack: OR-Tools branch and bound, exponential in the worst case, not the O(n·D) dynamic program.

## Sources

Each link was checked for reachability on 2026-11-17 with a plain GET. Reachability is not content
verification: the content of the sources was not re-read in this pass.

1. [Exact and heuristic solution algorithms for efficient emergency evacuation in areas with vulnerable populations](https://digitalcommons.unf.edu/unf_faculty_publications/824) (reachable)
2. [Bus evacuation: greedy, matheuristic and MIP (Erasmus thesis)](https://thesis.eur.nl/pub/73437/BSc2_Thesis_Daan_Olsthoorn.pdf) (reachable)
3. [Priority queues — Sedgewick & Wayne, Princeton](https://algs4.cs.princeton.edu/24pq/) · [Sorting cheatsheet](https://algs4.cs.princeton.edu/cheatsheet/) (reachable)
4. [Minimum-cost flow — Google OR-Tools](https://developers.google.com/optimization/flow/mincostflow) (reachable)
5. [CP-SAT solver — Google OR-Tools](https://developers.google.com/optimization/cp/cp_solver) (reachable)
6. [Interval-parameter mixed integer multi-objective programming for evacuation management](https://iaorifors.com/paper/68306) (returned HTTP 406 to the check; not verified)
7. [Knapsack — Google OR-Tools](https://developers.google.com/optimization/pack/knapsack) (reachable)
8. [Min-knapsack and covering programs](https://ar5iv.labs.arxiv.org/html/1903.00547) · [Covering and packing MILPs, supplier selection](https://arxiv.org/html/2512.02571v2) (reachable)
9. [Particle swarm for flash-flood vehicle assignment (survey listing)](https://core.ac.uk/works/77572610) (returned HTTP 403 to the check; not verified)
