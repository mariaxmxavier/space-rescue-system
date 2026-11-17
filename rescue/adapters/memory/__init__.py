"""In-memory adapters: the default implementations of every port.

What: re-exports ``MemoryTransactionStore``, ``ZeroClock`` and ``SequenceIdSource``.

When: imported in production code only by the composition root, ``rescue.bootstrap``, which
builds one of each per run; tests import them directly.

Why: the problem needs no database or real clock; in-memory, deterministic adapters keep runs
reproducible and double as the test fakes.
"""

from rescue.adapters.memory.clock import ZeroClock
from rescue.adapters.memory.id_source import SequenceIdSource
from rescue.adapters.memory.transaction_store import MemoryTransactionStore

__all__ = ["MemoryTransactionStore", "SequenceIdSource", "ZeroClock"]
