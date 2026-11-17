"""CP-SAT allocator, re-exported for the registry.

Imported by the algorithms package to register the integer-optimisation strategy.
"""

from rescue.mobilisation.algorithms.cp_sat.allocate import allocate

__all__ = ["allocate"]
