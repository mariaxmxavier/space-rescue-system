"""Priority-queue allocator, re-exported for the registry.

Imported by the algorithms package to register the heap-based earliest-arrival strategy.
"""

from rescue.mobilisation.algorithms.priority_queue.allocate import allocate

__all__ = ["allocate"]
