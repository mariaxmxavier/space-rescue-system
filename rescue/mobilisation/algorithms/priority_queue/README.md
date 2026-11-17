# Priority-queue allocator

The priority-queue family makes the same choice as greedy earliest-arrival: the earliest-arriving
ship gets seats first, and ties go to the lower ship id. The difference is the mechanism. The
candidates are kept in a min-heap keyed by `(arrival, ship_id)`, and the allocator pops the
smallest key until the demand is met or the heap is empty.

Diagram: [diagram.mmd](diagram.mmd). Rationale: [research.md](../../../../specs/006-mobilisation-conformance/research.md).
The reference it must agree with is [greedy](../greedy/README.md).

## Worked heap example

Demand 6, decision time 0. Four ships (the same snapshot as the greedy example, with ship D added):

| Ship | Allocatable seats | Arrival | Held quote |
|---|---|---|---|
| A | 4 | 10 | none |
| B | 5 | 12 | none |
| D | 2 | 9 | none |
| C | 3 | 8 | 3 seats, held |

Each candidate enters the heap as `(arrival, ship_id, candidate)`. `heapify` arranges the entries
in heap order, and then each `heappop` removes the smallest. The real output:

```
heap after heapify: [(8, 'C'), (10, 'A'), (9, 'D'), (12, 'B')]
pop order: [(8, 'C'), (9, 'D'), (10, 'A'), (12, 'B')]
priority_queue allocations: [('C', 3), ('D', 2), ('A', 1), ('B', 0)]
greedy earliest allocations: [('C', 3), ('D', 2), ('A', 1), ('B', 0)]
equal: True
trace: inputs None {'candidates': '4', 'demand': '6'}
trace: pick C {'seats': '3'}
trace: pick D {'seats': '2'}
trace: pick A {'seats': '1'}
trace: skip B {'reason': 'not_chosen'}
trace: result None {'seats': '6', 'remaining_demand': '0'}
```

C's held quote fits, so it takes 3 seats. D takes 2. A gives the last seat it needs (1 of its 4).
B is popped last with nothing left to fill, so it is skipped as `not_chosen`.

## Complexity

- Building the heap: `heapify` is O(n) for n candidates.
- Each `heappop` is O(log n).
- The loop pops every candidate, because the allocator does not stop when the demand is met. Each
  pop still runs in O(1) on the seat rules, so the whole call is O(n log n) time and O(n) space.

The greedy family sorts once and costs the same O(n log n). The heap form pays off when the same
structure is extended to incremental updates. This family does not do that (see Limitations).

## Snapshot rebuilding

The heap is built from the input candidates on every call. Nothing is kept between calls, so an
availability change is picked up the next time the decision runs. That keeps the function pure and
makes the result a function of the snapshot alone.

## Deterministic ordering and traces

The key `(arrival, ship_id)` is a total order, so equal arrivals resolve by ship id and the
allocation is deterministic. The trace holds:

- `inputs`: the candidate count and the unmet demand.
- one `pick` or `skip` step per candidate, in pop order. A skip carries the static reason or
  `not_chosen`.
- `result`: the seats allocated and the demand that remains.

Unlike greedy, the trace has no `order` step, because the pop sequence is the order. The contract
asks only for one step per candidate and a final result.

## Limitations

- The family does not optimise across ships. It never goes back to change an earlier choice, so it
  can leave seats that a different combination would cover.
- A persistent heap would need updates when a ship's availability changes. This family rebuilds
  the heap instead, which is simple and correct but costs O(n) on every call, however small the
  change.
- The heap entry is `(arrival, ship_id, candidate)`. Two candidates with the same arrival and the
  same ship id would make `heapq` compare the candidates and fail. Candidate ship ids are unique
  by the decision service's input rules, so the case is not reachable through the service.
