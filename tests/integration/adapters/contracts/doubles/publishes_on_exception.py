"""Seeded broken ``TransactionStore`` double that publishes a corrupted state when an operation raises.

What: one class, ``PublishesOnException``, used as the broken store in the transaction-store contract.

When: imported only by ``test_transaction_store_contract.py``.

Why: a contract check that cannot fail proves nothing; this double shows the check catches a store
that publishes on failure.
"""

from dataclasses import replace

from rescue.adapters.ports import TransactionStore
from rescue.application.state import RunState


class PublishesOnException(TransactionStore):
    """A deliberately broken store that publishes a corrupted state when the operation raises.

    What: after a ``RuntimeError`` it replaces the published state with a corrupted one, then re-raises.

    When: used only by the test proving that the contract check fails on a broken store.

    Why: the seeded fault the transaction-store contract must catch.
    """

    def __init__(self, state: RunState) -> None:
        """Start with ``state`` as the published state.

        What: stores the starting state.

        When: called once by the test that builds the broken store.

        Why: the broken store needs a starting state to corrupt.
        """
        self.state = state

    def transact(self, operation):
        """Apply ``operation``, publishing a corrupted state if it raises.

        What: runs the operation; on ``RuntimeError`` it publishes a corrupted state, then re-raises.

        When: called by the contract check in place of the memory store's transact.

        Why: the seeded fault the contract must catch.
        """
        try:
            self.state, result = operation(self.state)
        except RuntimeError:
            self.state = replace(self.state, command_index=("lost",))
            raise
        return result
