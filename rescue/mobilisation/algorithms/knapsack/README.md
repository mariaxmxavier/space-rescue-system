# Knapsack allocator

The knapsack family treats each ship as one item of a 0/1 knapsack. Its weight and value are the
ship's whole offer, and the capacity is the unmet demand. The OR-Tools `KnapsackSolver`
(branch and bound) picks the set of ships whose offers cover the most demand without going over.

Diagram: [diagram.mmd](diagram.mmd). Rationale: [research.md](../../../../specs/006-mobilisation-conformance/research.md).

## Known limit: whole offers only

A ship's offer is never split. A ship either gives its full offer or nothing, so the knapsack can
cover less demand than the divisible families, which can take part of a ship's seats. This is a
known limit of the family, not a hidden fault. The shortfall is visible: the `result` step reports
the seats covered and the demand that remains.

## Offer rules

For each ship, the offer (the knapsack weight and value) is:

- zero when the ship has a static skip reason (unavailable, quote not held or quote expired at the
  decision time);
- the held quote's seats when the ship has a valid quote (the quote fits the ship's allocatable
  seats); zero when the quote is larger than the ship can give;
- otherwise the ship's allocatable seats.

Ships with zero offer are ineligible: they can never be chosen.

## Worked shortfall example

Demand 5, decision time 0. Three ships whose whole offers are 4, 4 and 3 seats:

| Ship | Offer | Arrival |
|---|---|---|
| P | 4 | 1 |
| Q | 4 | 2 |
| R | 3 | 3 |

No subset of whole offers covers exactly 5: 4 + 4 = 8 and 4 + 3 = 7 both overshoot, and 3 alone
covers less than 4. The best choice is one 4-seat offer. Ties are resolved by the item order
(arrival, then ship id), so P is chosen over Q. The output of the real allocator:

```
knapsack: [('P', 4), ('Q', 0), ('R', 0)] covered 4
greedy: [('P', 4), ('Q', 1), ('R', 0)] covered 5
trace: item P {'weight': '4', 'value': '4'}
trace: item Q {'weight': '4', 'value': '4'}
trace: item R {'weight': '3', 'value': '3'}
trace: model None {'items': '3', 'capacity': '5'}
trace: solver None {'status': 'optimal', 'seats': '4'}
trace: pick P {'seats': '4'}
trace: skip Q {'reason': 'not_chosen'}
trace: skip R {'reason': 'not_chosen'}
trace: result None {'seats': '4', 'remaining_demand': '1'}
```

Greedy, which may split the last offer, covers all 5 demanded seats by taking one seat from Q.
Knapsack covers 4, and the trace reports the 1 seat it could not cover. That is the limit, shown in
the output rather than hidden.

## Chosen-seat unused capacity

A chosen ship takes its full offer, so:

- for a ship without a quote, the seats taken equal its allocatable seats and its unused capacity is
  zero;
- for a ship with a held quote, the seats taken are the quote's seats and its unused capacity is its
  allocatable seats minus the quote's seats.

## Deterministic tie-breaking

The items are sorted by `(arrival, ship_id)` before the solver runs. Among sets of equal value the
branch and bound keeps the earlier items, so the same chosen set comes back for every order of the
input. The tests check this across all input permutations of tied ships.

## Solver complexity

The solver is a branch-and-bound search. Its worst case is exponential in the number of items: each
ship can be in or out, and the search can visit many of the 2^n combinations. The algorithm does not
use dynamic programming, and this README does not describe any such bound. The tested scenarios are
small (at most five ships), where the search is fast; the measured runtime is in the US3 section of
the [quickstart](../../../../specs/006-mobilisation-conformance/quickstart.md).

## Status handling

- `empty`: the demand is zero or less, or every offer is zero. The solver is not run, and nothing is
  chosen.
- `optimal`: the solver proved the chosen set is the best.
- `feasible`: the solver returned a set that fits the demand without proving it best. The set is
  kept, because it is still feasible.

## Trace interpretation

- `item`: one per ship in sorted order, with its weight and value (the same number for knapsack).
- `model`: the number of items and the capacity (the demand).
- `solver`: the status and the seats covered by the chosen set.
- `pick` and `skip` per ship, then `result` with the seats covered and the demand left.
