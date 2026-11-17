"""Allocation values: seats given to each candidate by one allocator run.

Transient values, not in the Mobilisation diagrams.
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.mobilisation.models.algorithm_name import AlgorithmName
from rescue.mobilisation.models.trace_step import TraceStep
from rescue.values import Id, immutable_tuple, normalize_id, normalize_nonnegative_quantity


@dataclass(frozen=True, slots=True)
class Allocation:
    """Seats an allocator gives one ship, zero when the ship is not used.

    Produced once per candidate by an allocator and checked by the decision service.
    """

    ship_id: Id
    seats: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "ship_id", normalize_id(self.ship_id))
        object.__setattr__(self, "seats", normalize_nonnegative_quantity(self.seats))


@dataclass(frozen=True, slots=True)
class AllocationResult:
    """The outcome of one allocator run: allocations in rank order plus its trace.

    Returned by every allocator so the decision service can validate it, rank by its
    order and log its steps.
    """

    algorithm: AlgorithmName
    allocations: tuple[Allocation, ...]
    trace: tuple[TraceStep, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "algorithm", AlgorithmName(self.algorithm))
        object.__setattr__(self, "allocations", immutable_tuple(self.allocations))
        object.__setattr__(self, "trace", immutable_tuple(self.trace))
