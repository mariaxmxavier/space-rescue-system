"""Priority-queue allocator: pop ships from a min-heap of (arrival, ship id).

Called through the ALLOCATORS registry when a policy names priority_queue. It rebuilds the
heap from each input snapshot, so an availability change is picked up on the next call and
no queue state survives between calls. It agrees with greedy earliest arrival by design.
"""

from __future__ import annotations

import heapq

from rescue.mobilisation.algorithms.greedy.allocate import _seats_for
from rescue.mobilisation.models.algorithm_name import AlgorithmName
from rescue.mobilisation.models.allocation import Allocation, AllocationResult
from rescue.mobilisation.models.candidate import Candidate, arrival_instant
from rescue.mobilisation.models.skip_reason import SkipReason, static_skip_reason
from rescue.mobilisation.models.trace_step import TraceStep
from rescue.values import Instant

_ALGORITHM = AlgorithmName.PRIORITY_QUEUE


def allocate(candidates: tuple[Candidate, ...], demand: int, at: Instant) -> AllocationResult:
    """Fill demand by popping the earliest-arriving ship first, ties broken by ship id.

    Called by the decision service for the priority_queue strategy. The heap is built
    fresh from the candidates on every call; nothing is kept between calls.
    """
    heap = [(arrival_instant(c), c.ship_id, c) for c in candidates]
    heapq.heapify(heap)
    trace = [
        TraceStep(
            _ALGORITHM,
            "inputs",
            None,
            (("candidates", str(len(heap))), ("demand", str(demand))),
        )
    ]
    allocations: list[Allocation] = []
    remaining = demand
    while heap:
        _, _, candidate = heapq.heappop(heap)
        static = static_skip_reason(candidate, at)
        seats = 0 if static is not None else _seats_for(candidate, remaining)
        remaining -= seats
        allocations.append(Allocation(ship_id=candidate.ship_id, seats=seats))
        if seats > 0:
            trace.append(TraceStep(_ALGORITHM, "pick", candidate.ship_id, (("seats", str(seats)),)))
        else:
            reason = static if static is not None else SkipReason.NOT_CHOSEN
            trace.append(
                TraceStep(_ALGORITHM, "skip", candidate.ship_id, (("reason", str(reason)),))
            )
    trace.append(
        TraceStep(
            _ALGORITHM,
            "result",
            None,
            (("seats", str(demand - remaining)), ("remaining_demand", str(remaining))),
        )
    )
    return AllocationResult(
        algorithm=_ALGORITHM, allocations=tuple(allocations), trace=tuple(trace)
    )
