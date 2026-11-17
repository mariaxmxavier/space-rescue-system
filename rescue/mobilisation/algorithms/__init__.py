"""Allocator contract and the registry of available allocators.

Imported by the decision service to find the allocator for a policy strategy. Each allocator
is a pure function, so strategies can be swapped or compared without touching the service.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType

from rescue.mobilisation.algorithms.cp_sat import allocate as allocate_cp_sat
from rescue.mobilisation.algorithms.greedy import (
    allocate_earliest_arrival,
    allocate_largest_capacity,
)
from rescue.mobilisation.algorithms.knapsack import allocate as allocate_knapsack
from rescue.mobilisation.algorithms.min_cost_flow import allocate as allocate_min_cost_flow
from rescue.mobilisation.algorithms.priority_queue import allocate as allocate_priority_queue
from rescue.mobilisation.models.algorithm_name import AlgorithmName
from rescue.mobilisation.models.allocation import AllocationResult
from rescue.mobilisation.models.candidate import Candidate
from rescue.values import Instant

Allocator = Callable[[tuple[Candidate, ...], int, Instant], AllocationResult]

ALLOCATORS: Mapping[AlgorithmName, Allocator] = MappingProxyType(
    {
        AlgorithmName.EARLIEST_ARRIVAL: allocate_earliest_arrival,
        AlgorithmName.LARGEST_CAPACITY: allocate_largest_capacity,
        AlgorithmName.PRIORITY_QUEUE: allocate_priority_queue,
        AlgorithmName.MIN_COST_FLOW: allocate_min_cost_flow,
        AlgorithmName.CP_SAT: allocate_cp_sat,
        AlgorithmName.KNAPSACK: allocate_knapsack,
    }
)

__all__ = ["ALLOCATORS", "Allocator"]
