# Minimum-cost-flow allocator

The min-cost-flow family models the seats as flow. Each open ship carries flow from a source to
the mission through its own node, and the cost of a seat grows with how late the ship arrives. The
solver finds the flow that covers the residual demand at the lowest total cost, with OR-Tools
`SimpleMinCostFlow`.

Diagram: [diagram.mmd](diagram.mmd). Rationale: [research.md](../../../../specs/006-mobilisation-conformance/research.md).

## How the network is built

1. **Held quotes first.** A quote is all or nothing, and a flow cannot split it. Every eligible
   held quote is therefore decided before any open ship is considered, in arrival order, whatever
   the open ships' arrival times. This is the design fixed by the plan; its consequence is the first
   limitation below. A quote takes its seats only when they fit the remaining demand and the ship's
   allocatable seats.
2. **Residual demand.** The demand left after the quotes is the supply of the network.
3. **Arcs.** Each open ship (no quote, allocatable seats above zero) gets a node `position + 2`,
   where `position` is its index in `(arrival, ship_id)` order. Source 0 and sink 1 are the other
   two nodes, so the network has n + 2 nodes for n open ships. There are two arcs per open ship:
   source to ship with the ship's allocatable seats as capacity and zero cost, and ship to sink with
   the residual supply as capacity and the unit cost below.
4. **Cost.** The arrival cost is the time from the decision to the arrival, in whole seconds,
   rounded up and never negative: `ceil(max(arrival - at, 0))`. `SimpleMinCostFlow` takes integers
   only, which is why the time is rounded. The unit cost adds the ship's position:
   `arrival_cost * n + position`, where n is the number of open ships. Because position is smaller
   than n, arrival still dominates, and ships that arrive within the same whole second are ordered
   by `(arrival, ship_id)`. The cost is capped at the 64-bit integer limit, so an enormous arrival
   gives a clear solver status rather than an overflow.

## Worked example

Demand 6, decision time 0. The ships from the greedy example, with ship D added:

| Ship | Allocatable seats | Arrival | Held quote |
|---|---|---|---|
| A | 4 | 10 | none |
| B | 5 | 12 | none |
| D | 2 | 9 | none |
| C | 3 | 8 | 3 seats, held |

C's quote fits, so 3 seats are preallocated and 3 remain as supply. The open ships are D (cost
`9 * 3 + 0 = 27`), A (`10 * 3 + 1 = 31`) and B (`12 * 3 + 2 = 38`). The cheapest flow sends 2 seats
through D and 1 through A, and B receives nothing. The output of the real allocator:

```
allocations: [('C', 3), ('D', 2), ('A', 1), ('B', 0)]
trace: inputs None {'candidates': '4', 'demand': '6'}
trace: quote C {'offered': '3', 'seats': '3'}
trace: arc D {'capacity': '2', 'arrival_cost_s': '9', 'unit_cost': '27'}
trace: arc A {'capacity': '4', 'arrival_cost_s': '10', 'unit_cost': '31'}
trace: arc B {'capacity': '5', 'arrival_cost_s': '12', 'unit_cost': '38'}
trace: model None {'ships': '3', 'supply': '3'}
trace: status None {'status': 'OPTIMAL'}
trace: pick C {'seats': '3'}
trace: pick D {'seats': '2'}
trace: pick A {'seats': '1'}
trace: skip B {'reason': 'not_chosen'}
trace: result None {'seats': '6', 'remaining_demand': '0'}
```

## Solver complexity

`SimpleMinCostFlow` solves the network in one call per decision. The network has n + 2 nodes and
2n arcs for n open ships. This README makes no worst-case bound claim for the solver. The measured
runtime is the practical figure: on the five-ship comparison scenarios the slowest sample was
0.31 ms (see the US3 section of the [quickstart](../../../../specs/006-mobilisation-conformance/quickstart.md)).

## Deterministic ordering

The arcs are numbered by `(arrival, ship_id)`. The result lists the selected ships first, then the
unselected ones, and each group is sorted by `(arrival, ship_id)`. The same inputs give the same
allocation, including on ties.

## Statuses

- `OPTIMAL` and `FEASIBLE` are usable: the flow on each arc is read as the ship's seats.
- Any other status (for example infeasible or bad cost range) gives every open ship zero seats.
  The held quotes still stand, because they were decided before the solver ran. The trace records
  the status name.

## Trace interpretation

- `inputs`: candidate count and demand.
- `quote`: the decision for each held quote, with its offered seats and the seats taken.
- `arc`: one per open ship, with its capacity, arrival cost in seconds and unit cost.
- `model`: the number of open ships and the supply sent into the network.
- `status`: the solver status name.
- `pick` and `skip` per ship, then `result` with the seats covered and the demand left.

## Limitations

### Quotes are fixed before open ships, whatever their arrival

Every eligible quote is decided first, so a quote that arrives late can take seats that an earlier
open ship would have given. Demand 5, one open ship A (5 seats, arrival 1) and one held quote Q
(3 seats, arrival 50). The output of the real allocator:

```
min_cost_flow: [('A', 2), ('Q', 3)]   last seat at 50
greedy:        [('A', 5), ('Q', 0)]   last seat at 1
```

Both cover the demand, but min-cost flow takes the late quote and finishes at 50 instead of 1.
Greedy ranks the quote and the open ship together by arrival, so it does not share this limit.

### Quotes are preallocated greedily, not optimised with the flow

Held quotes are not optimised together with the flow. They are fixed greedily in arrival order, so a
quote that fits can block a better combination of quotes. With demand 5, quote A (3 seats, arrival
1) and quote B (4 seats, arrival 2), and no open ship, the allocator takes A because it arrives
first. The output of the real allocator:

```
allocations: [('A', 3), ('B', 0)]
covered: 3
```

After A's 3 seats, B's 4 no longer fits the remaining 2, so the allocator covers 3. Taking B alone
covers 4. An exact solver that optimised the quotes indivisibly with the flow could find that
better answer; this family does not. The other families do not share the limit in the same way:
the CP-SAT family models quotes as whole-or-nothing variables, and the knapsack family chooses
whole offers.
