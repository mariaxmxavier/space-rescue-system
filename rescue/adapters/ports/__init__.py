"""Ports: abstract capabilities the application asks the outside world for.

What: re-exports ``TransactionStore``, ``Clock`` and ``IdSource``, one abstract class per module.

When: imported by ``rescue.application`` to type its dependencies, and by every adapter that
implements one of them.

Why: the application depends on these abstractions, never on a concrete adapter, so any
implementation that honours the port can be injected.
"""

from rescue.adapters.ports.clock import Clock
from rescue.adapters.ports.id_source import IdSource
from rescue.adapters.ports.transaction_store import TransactionStore

__all__ = ["Clock", "IdSource", "TransactionStore"]
