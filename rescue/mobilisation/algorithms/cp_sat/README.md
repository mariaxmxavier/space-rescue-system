# CP-SAT allocator

The CP-SAT family chooses the seats for every ship in one integer model, solved with OR-Tools
`CpSolver`. It maximises the seats covered, then minimises the last arrival among the ships used,
then the number of ships used. Where two answers are still equal, ship ids decide. Each stage is a
separate solve, so the result is the lexicographic optimum of those criteria.

Diagram: [diagram.mmd](diagram.mmd). Rationale: [research.md](../../../../specs/006-mobilisation-conformance/research.md).
Measured runtimes: [quickstart](../../../../specs/006-mobilisation-conformance/quickstart.md) (US3 section).

## The model

For each usable ship i (not a static skip) the model has:

- `x_i` in `[0, cap_i]`: the seats taken from ship i, where `cap_i` is its allocatable seats.
- `use_i` in `{0, 1}`: whether ship i is used at all.
- `x_i <= cap_i * use_i` and `x_i >= use_i`: a ship is used if and only if it gives seats.
- For a ship with a held quote, `x_i == q_i * use_i`: the quote is taken whole or not at all.
- `latest >= arrival_i * use_i`, where `latest` is the last-arrival variable.
- Across ships, `sum(x_i) <= demand`.

Arrival times enter the model as integer offsets from the earliest usable arrival (see Integer
time below), so `latest` is the lateness of the last ship used, not an absolute time.

## Objective, in stages

The solver runs one stage per objective. Each stage is solved, and its optimum is fixed as a
constraint before the next stage starts.

1. **Coverage.** Maximise `sum(x_i)`. This is the seats covered; nothing else matters yet.
2. **Last arrival, then fewest ships.** Minimise `latest * (n + 1) + sum(use_i)`, where n is the
   number of usable ships. The weight `n + 1` makes the last arrival dominate: the ship count is at
   most n, so one more unit of `latest` always outweighs any count.
3. **Ship-id ties.** For each usable ship in ascending ship id order, maximise that ship's `x_i`,
   then fix it. Among answers that are still equal, the lowest ship id wins, and the rule is enforced
   by its own stage, not by the order the solver happens to return.

The tie stages cost n solves on top of the two objective stages, so a decision is n + 2 solves.

## Integer time

CP-SAT takes integers only. The arrival offsets are taken from the earliest usable arrival, and
each is scaled by `10^k`, where k is the largest number of decimal places among the offsets. The
scaling is deterministic, and exact while the offsets fit the default 28-digit Decimal precision; no
offset is rounded within that range. The cost is that arrivals with many decimal places give large
coefficients in the model. A scaled offset above 2^40 is rejected with a `DomainValidationError`
before the model is built, because the solver's integers must stay in range.

## Worked example

Demand 6, decision time 0. Three ships:

| Ship | Allocatable seats | Arrival |
|---|---|---|
| X | 6 | 12 |
| Y | 3 | 5 |
| Z | 3 | 9 |

Coverage 6 is reachable by X alone, or by Y and Z together. The last-arrival stage decides: {Y, Z}
ends at 9 and {X} ends at 12, so Y and Z win. The output of the real allocator:

```
allocations: [('Y', 3), ('Z', 3), ('X', 0)]
trace: model None {'usable': '3', 'demand': '6', 'time_scale': '1'}
trace: status None {'stage': 'coverage', 'status': 'OPTIMAL'}
trace: status None {'stage': 'arrival_then_ships', 'status': 'OPTIMAL'}
trace: status X {'stage': 'ship_id_tie', 'status': 'OPTIMAL'}
trace: status Y {'stage': 'ship_id_tie', 'status': 'OPTIMAL'}
trace: status Z {'stage': 'ship_id_tie', 'status': 'OPTIMAL'}
trace: pick Y {'seats': '3'}
trace: pick Z {'seats': '3'}
trace: skip X {'reason': 'not_chosen'}
trace: result None {'seats': '6', 'remaining_demand': '0'}
```

## Solver status handling

- `OPTIMAL` and `FEASIBLE` are accepted at every stage.
- Any other status (for example `INFEASIBLE` or `UNKNOWN`) stops the solve and gives every ship zero
  seats. The status is recorded in a `status` trace step with its stage name.
- Each stage records its own status, so a failure is visible at the stage where it happened.

## Complexity and runtime

CP-SAT has no polynomial worst-case bound in general. The model has n integer seat variables, n
boolean use variables, one integer last-arrival variable and n + 2 solves. The practical runtime at
the scenario sizes used here is measured, not bounded: the slowest cp_sat sample across the
five-ship comparison scenarios was 12.7 ms (see the US3 section of the
[quickstart](../../../../specs/006-mobilisation-conformance/quickstart.md)).

## Determinism

`num_workers = 1` and `random_seed = 0` make repeated runs return the same result. The
ship-id tie stages decide equal optima, so the answer does not depend on the order of the input.

## Trace interpretation

- `model`: the number of usable ships, the demand and the time scale used for integer arrivals.
- `status` per stage: the stage name, the ship id for the tie stages, and the solver status. A
  non-usable status ends the decision with no seats.
- `pick` and `skip` per ship, then `result` with the seats covered and the demand left.
