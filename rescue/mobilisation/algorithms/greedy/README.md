# Greedy allocators

Two strategies share one rule: sort the candidate ships by a key, then fill the unmet demand in
that order. `earliest_arrival` is the default and reproduces the behaviour the mobilisation
decision had before the algorithm boundary existed. `largest_capacity` is the legacy alternative,
kept available through the registry and not shown as a default comparison row.

Diagram: [diagram.mmd](diagram.mmd). Rationale: [research.md](../../../../specs/006-mobilisation-conformance/research.md).

## Ordering

| Strategy | Sort key | Ties |
|---|---|---|
| `earliest_arrival` (default) | arrival time, then ship id | ship id ascending |
| `largest_capacity` (legacy) | allocatable seats (largest first), then arrival, then ship id | ship id ascending |

Arrival is the record time of the ship's offer plus its estimate. Ship id is the last key, so the
order is total and the same inputs always give the same allocation.

## How each ship is decided

Walk the sorted candidates with the demand still unmet:

1. A ship with a static skip reason (unavailable, quote not held, or quote expired at the decision
   time) gets zero seats.
2. A ship with a held quote is taken whole or not at all. It gets its quoted seats only when those
   seats fit both the remaining demand and the ship's allocatable seats. Otherwise it gets zero.
3. A ship with no quote gets the smaller of its allocatable seats and the remaining demand.
4. A ship with zero seats after these rules is recorded as `not_chosen`.

## Worked example

Demand 6, decision time 0. Three ships:

| Ship | Allocatable seats | Arrival | Held quote |
|---|---|---|---|
| A | 4 | 10 | none |
| B | 5 | 12 | none |
| C | 3 | 8 | 3 seats, held |

Earliest arrival sorts C (8), A (10), B (12). C's quote fits, so it takes 3 seats and 3 remain. A
gives 3 and nothing remains for B. The output of the real allocator:

```
earliest_arrival
  allocations: [('C', 3), ('A', 3), ('B', 0)]
  trace: inputs None {'candidates': '3', 'demand': '6'}
  trace: order None {'ship_ids': 'C,A,B'}
  trace: pick C {'seats': '3'}
  trace: pick A {'seats': '3'}
  trace: skip B {'reason': 'not_chosen'}
  trace: result None {'seats': '6', 'remaining_demand': '0'}
```

Largest capacity sorts B (5 seats), A (4), C (3). B takes 5, A takes the last 1, and C's held
quote no longer fits the remaining demand:

```
largest_capacity
  allocations: [('B', 5), ('A', 1), ('C', 0)]
  trace: inputs None {'candidates': '3', 'demand': '6'}
  trace: order None {'ship_ids': 'B,A,C'}
  trace: pick B {'seats': '5'}
  trace: pick A {'seats': '1'}
  trace: skip C {'reason': 'not_chosen'}
  trace: result None {'seats': '6', 'remaining_demand': '0'}
```

Both strategies cover the demand here, but they reach it through different ships. That difference
is the reason the default is a policy choice, not a fixed rule.

## Complexity

Sorting dominates: O(n log n) comparisons for n candidates. Each candidate then costs O(1) (a skip
check, a quote check and a min). The whole call is O(n log n) time and O(n) space for the sorted
copy and the trace.

## Trace interpretation

The trace is a tuple of steps in order:

- `inputs`: how many candidates and the unmet demand the allocator received.
- `order`: the ship ids in the sequence the sort produced.
- `pick`: a ship that received seats, with the seats it took.
- `skip`: a ship that received zero seats, with the reason. A static reason is kept; otherwise the
  reason is `not_chosen`.
- `result`: the seats allocated in total and the demand that remains.

The decision service explains zero seats more fully (for example `exhausted` or
`quote_exceeds_remaining_demand`). The allocator records only what it decided, so its skip reason
can be `not_chosen` where the service later names a finer reason.

## Limitations

- Greedy never revisits a choice. A ship taken early stays taken, even when a different combination
  would cover more of the demand. The solver families (min-cost flow, CP-SAT, knapsack) can find
  those combinations.
- The rule ignores arrival time after the sort: a later ship never displaces an earlier one.
