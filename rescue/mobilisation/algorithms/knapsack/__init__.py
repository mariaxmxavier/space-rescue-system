"""Knapsack allocator, re-exported for the registry.

Imported by the algorithms package to register the whole-ship 0/1 knapsack strategy.
"""

from rescue.mobilisation.algorithms.knapsack.allocate import allocate

__all__ = ["allocate"]
