"""Knapsack allocator: choose whole ship offers that cover the most demand without overshoot.

Called through the ALLOCATORS registry when a policy names knapsack. Each ship is one 0/1
item whose weight and value are its full offer (held quote seats, else allocatable seats),
solved by the OR-Tools branch-and-bound KnapsackSolver with capacity equal to the demand.

Known limit: a ship's offer is never split, so knapsack may cover less demand than the
other algorithms. The shortfall is reported as remaining demand in the result step.
"""

from __future__ import annotations

from ortools.algorithms.python.knapsack_solver import KnapsackSolver, SolverType

from rescue.mobilisation.models.algorithm_name import AlgorithmName
from rescue.mobilisation.models.allocation import Allocation, AllocationResult
from rescue.mobilisation.models.candidate import Candidate, arrival_instant
from rescue.mobilisation.models.skip_reason import SkipReason, static_skip_reason
from rescue.mobilisation.models.trace_step import TraceStep
from rescue.values import Instant

ALGORITHM = AlgorithmName.KNAPSACK


def _offer(candidate: Candidate, at: Instant) -> int:
    if static_skip_reason(candidate, at) is not None:
        return 0
    quote = candidate.quote
    if quote is None:
        return candidate.allocatable_seats
    return quote.offered_seats if quote.offered_seats <= candidate.allocatable_seats else 0


def _solve(weights: list[int], demand: int) -> tuple[str, frozenset[int]]:
    if demand <= 0 or not any(weights):
        return "empty", frozenset()
    solver = KnapsackSolver(SolverType.KNAPSACK_MULTIDIMENSION_BRANCH_AND_BOUND_SOLVER, "knapsack")
    solver.init(weights, [weights], [demand])
    solver.solve()
    status = "optimal" if solver.is_solution_optimal() else "feasible"
    chosen = frozenset(i for i, w in enumerate(weights) if w and solver.best_solution_contains(i))
    return status, chosen


def allocate(candidates: tuple[Candidate, ...], demand: int, at: Instant) -> AllocationResult:
    """Pick whole offers that maximise covered seats up to demand, chosen ships ranked first.

    Called by the decision service for the knapsack strategy. Items are sorted by (arrival,
    ship_id) so the solver, which keeps earlier items among equal-value sets, always returns
    the same chosen set. A non-optimal solver result is kept, as it is still feasible.
    """
    ordered = sorted(candidates, key=lambda c: (arrival_instant(c), c.ship_id))
    weights = [_offer(candidate, at) for candidate in ordered]
    trace = [
        TraceStep(ALGORITHM, "item", c.ship_id, (("weight", str(w)), ("value", str(w))))
        for c, w in zip(ordered, weights, strict=True)
    ]
    trace.append(
        TraceStep(
            ALGORITHM, "model", None, (("items", str(len(ordered))), ("capacity", str(demand)))
        )
    )
    status, chosen = _solve(weights, demand)
    covered = sum(weights[i] for i in chosen)
    trace.append(
        TraceStep(ALGORITHM, "solver", None, (("status", status), ("seats", str(covered))))
    )
    ranked = [i for i in range(len(ordered)) if i in chosen]
    ranked += [i for i in range(len(ordered)) if i not in chosen]
    allocations = []
    for i in ranked:
        candidate = ordered[i]
        seats = weights[i] if i in chosen else 0
        allocations.append(Allocation(ship_id=candidate.ship_id, seats=seats))
        if seats:
            trace.append(TraceStep(ALGORITHM, "pick", candidate.ship_id, (("seats", str(seats)),)))
        else:
            reason = static_skip_reason(candidate, at) or SkipReason.NOT_CHOSEN
            trace.append(
                TraceStep(ALGORITHM, "skip", candidate.ship_id, (("reason", str(reason)),))
            )
    trace.append(
        TraceStep(
            ALGORITHM,
            "result",
            None,
            (("seats", str(covered)), ("remaining_demand", str(demand - covered))),
        )
    )
    return AllocationResult(algorithm=ALGORITHM, allocations=tuple(allocations), trace=tuple(trace))
