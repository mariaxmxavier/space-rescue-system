"""Greedy allocators, re-exported for the registry.

Imported by the algorithms package to register the two rank-and-fill strategies.
"""

from rescue.mobilisation.algorithms.greedy.allocate import (
    allocate_earliest_arrival,
    allocate_largest_capacity,
)

__all__ = ["allocate_earliest_arrival", "allocate_largest_capacity"]
