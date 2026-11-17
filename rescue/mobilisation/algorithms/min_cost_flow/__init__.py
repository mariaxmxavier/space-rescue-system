"""Min-cost flow allocator, re-exported for the registry.

Imported by the algorithms package to register the OR-Tools flow strategy.
"""

from rescue.mobilisation.algorithms.min_cost_flow.allocate import allocate

__all__ = ["allocate"]
