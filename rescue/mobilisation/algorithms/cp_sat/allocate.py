"""CP-SAT allocator: choose ships and seat counts by integer optimisation.

Called through the ALLOCATORS registry when a policy names cp_sat. It solves in
lexicographic stages: maximise covered seats, then minimise the last arrival and the
number of ships, then break equal optima by ship id, so the choice is optimal and
deterministic. Arrival seconds are made integers exactly: each usable arrival minus the
earliest one, times 10 to the largest number of decimal places present.
"""

from __future__ import annotations

from decimal import Decimal

from ortools.sat.python import cp_model

from rescue.mobilisation.models.algorithm_name import AlgorithmName
from rescue.mobilisation.models.allocation import Allocation, AllocationResult
from rescue.mobilisation.models.candidate import Candidate, arrival_instant
from rescue.mobilisation.models.skip_reason import SkipReason, static_skip_reason
from rescue.mobilisation.models.trace_step import TraceStep
from rescue.values import DomainValidationError, Instant

_ALGORITHM = AlgorithmName.CP_SAT
_SOLVED = (cp_model.OPTIMAL, cp_model.FEASIBLE)
_MAX_SCALED_OFFSET = 2**40


def _integer_arrivals(usable: tuple[Candidate, ...]) -> tuple[tuple[int, ...], int]:
    if not usable:
        return (), 1
    earliest = min(arrival_instant(candidate) for candidate in usable)
    offsets = tuple(arrival_instant(candidate) - earliest for candidate in usable)
    places = max(max(0, -int(offset.as_tuple().exponent)) for offset in offsets)
    scale = 10**places
    scaled = tuple(int(offset * Decimal(scale)) for offset in offsets)
    if max(scaled) > _MAX_SCALED_OFFSET:
        raise DomainValidationError("arrival offsets exceed the solver's integer range")
    return scaled, scale


def _solve(usable: tuple[Candidate, ...], demand: int, trace: list[TraceStep]) -> dict[str, int]:
    arrivals, scale = _integer_arrivals(usable)
    model = cp_model.CpModel()
    seats: dict[str, cp_model.IntVar] = {}
    uses: list[cp_model.IntVar] = []
    latest = model.new_int_var(0, max(arrivals, default=0), "last_arrival")
    for candidate, arrival in zip(usable, arrivals, strict=True):
        cap = candidate.allocatable_seats
        x = model.new_int_var(0, cap, f"x_{candidate.ship_id}")
        use = model.new_bool_var(f"use_{candidate.ship_id}")
        model.add(x <= cap * use)
        model.add(x >= use)
        if candidate.quote is not None:
            model.add(x == candidate.quote.offered_seats * use)
        model.add(latest >= arrival * use)
        seats[candidate.ship_id] = x
        uses.append(use)
    covered = cp_model.LinearExpr.sum(list(seats.values()))
    model.add(covered <= demand)
    trace.append(
        TraceStep(
            _ALGORITHM,
            "model",
            None,
            (("usable", str(len(usable))), ("demand", str(demand)), ("time_scale", str(scale))),
        )
    )
    stages = [
        ("coverage", None, covered, True),
        (
            "arrival_then_ships",
            None,
            latest * (len(usable) + 1) + cp_model.LinearExpr.sum(uses),
            False,
        ),
    ] + [("ship_id_tie", ship_id, seats[ship_id], True) for ship_id in sorted(seats)]
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.random_seed = 0
    for stage, ship_id, objective, maximise in stages:
        model.maximize(objective) if maximise else model.minimize(objective)
        status = solver.solve(model)
        trace.append(
            TraceStep(_ALGORITHM, "status", ship_id, (("stage", stage), ("status", status.name)))
        )
        if status not in _SOLVED:
            return {}
        model.add(objective == int(solver.value(objective)))
    return {ship_id: int(solver.value(x)) for ship_id, x in seats.items()}


def allocate(candidates: tuple[Candidate, ...], demand: int, at: Instant) -> AllocationResult:
    """Choose seats per ship by CP-SAT: most seats, then earliest last arrival, then fewest ships.

    Called by the decision service for the cp_sat strategy. Equal optima give the most
    seats to the lowest ship id first. A solver status other than OPTIMAL or FEASIBLE
    allocates nothing; every status is recorded in the trace.
    """
    usable = tuple(
        candidate for candidate in candidates if static_skip_reason(candidate, at) is None
    )
    trace: list[TraceStep] = []
    chosen = _solve(usable, demand, trace)
    ordered = sorted(
        candidates,
        key=lambda c: (chosen.get(c.ship_id, 0) == 0, arrival_instant(c), c.ship_id),
    )
    allocations: list[Allocation] = []
    for candidate in ordered:
        seats = chosen.get(candidate.ship_id, 0)
        allocations.append(Allocation(ship_id=candidate.ship_id, seats=seats))
        if seats > 0:
            trace.append(TraceStep(_ALGORITHM, "pick", candidate.ship_id, (("seats", str(seats)),)))
        else:
            reason = static_skip_reason(candidate, at) or SkipReason.NOT_CHOSEN
            trace.append(
                TraceStep(_ALGORITHM, "skip", candidate.ship_id, (("reason", str(reason)),))
            )
    total = sum(allocation.seats for allocation in allocations)
    trace.append(
        TraceStep(
            _ALGORITHM,
            "result",
            None,
            (("seats", str(total)), ("remaining_demand", str(demand - total))),
        )
    )
    return AllocationResult(
        algorithm=_ALGORITHM, allocations=tuple(allocations), trace=tuple(trace)
    )
