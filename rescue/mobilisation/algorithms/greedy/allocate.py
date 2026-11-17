"""Greedy allocators: rank candidates by one key and fill demand in that order.

Called through the ALLOCATORS registry when a policy names earliest_arrival or
largest_capacity. They keep the original selection rules as pure functions of the
candidates, the unmet demand and the decision time, with no I/O and no clock.
"""

from __future__ import annotations

from collections.abc import Callable

from rescue.mobilisation.models.algorithm_name import AlgorithmName
from rescue.mobilisation.models.allocation import Allocation, AllocationResult
from rescue.mobilisation.models.candidate import Candidate, arrival_instant
from rescue.mobilisation.models.skip_reason import SkipReason, static_skip_reason
from rescue.mobilisation.models.trace_step import TraceStep
from rescue.values import Instant

SortKey = Callable[[Candidate], tuple[object, ...]]


def _earliest_arrival_key(candidate: Candidate) -> tuple[object, ...]:
    return (arrival_instant(candidate), candidate.ship_id)


def _largest_capacity_key(candidate: Candidate) -> tuple[object, ...]:
    return (-candidate.allocatable_seats, arrival_instant(candidate), candidate.ship_id)


def _seats_for(candidate: Candidate, remaining: int) -> int:
    if remaining <= 0 or candidate.allocatable_seats <= 0:
        return 0
    quote = candidate.quote
    if quote is None:
        return min(candidate.allocatable_seats, remaining)
    if quote.offered_seats > remaining or quote.offered_seats > candidate.allocatable_seats:
        return 0
    return quote.offered_seats


def _allocate(
    algorithm: AlgorithmName,
    key: SortKey,
    candidates: tuple[Candidate, ...],
    demand: int,
    at: Instant,
) -> AllocationResult:
    ordered = tuple(sorted(candidates, key=key))
    trace = [
        TraceStep(
            algorithm,
            "inputs",
            None,
            (("candidates", str(len(ordered))), ("demand", str(demand))),
        ),
        TraceStep(
            algorithm,
            "order",
            None,
            (("ship_ids", ",".join(candidate.ship_id for candidate in ordered)),),
        ),
    ]
    allocations: list[Allocation] = []
    remaining = demand
    for candidate in ordered:
        static = static_skip_reason(candidate, at)
        seats = 0 if static is not None else _seats_for(candidate, remaining)
        remaining -= seats
        allocations.append(Allocation(ship_id=candidate.ship_id, seats=seats))
        if seats > 0:
            trace.append(TraceStep(algorithm, "pick", candidate.ship_id, (("seats", str(seats)),)))
        else:
            reason = static if static is not None else SkipReason.NOT_CHOSEN
            trace.append(
                TraceStep(algorithm, "skip", candidate.ship_id, (("reason", str(reason)),))
            )
    trace.append(
        TraceStep(
            algorithm,
            "result",
            None,
            (("seats", str(demand - remaining)), ("remaining_demand", str(remaining))),
        )
    )
    return AllocationResult(algorithm=algorithm, allocations=tuple(allocations), trace=tuple(trace))


def allocate_earliest_arrival(
    candidates: tuple[Candidate, ...], demand: int, at: Instant
) -> AllocationResult:
    """Fill demand from the ships that arrive first, ties broken by ship id.

    Called by the decision service for the earliest_arrival strategy.
    """
    return _allocate(AlgorithmName.EARLIEST_ARRIVAL, _earliest_arrival_key, candidates, demand, at)


def allocate_largest_capacity(
    candidates: tuple[Candidate, ...], demand: int, at: Instant
) -> AllocationResult:
    """Fill demand from the ships with most allocatable seats, then earliest arrival.

    Called by the decision service for the largest_capacity strategy.
    """
    return _allocate(AlgorithmName.LARGEST_CAPACITY, _largest_capacity_key, candidates, demand, at)
