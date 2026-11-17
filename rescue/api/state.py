"""Read a consistent committed snapshot from one run."""

from rescue.adapters.ports import TransactionStore
from rescue.state import RunState


def read_run_state(store: TransactionStore) -> RunState:
    """Return the complete committed state through the store's read-only contract."""
    return store.snapshot()
