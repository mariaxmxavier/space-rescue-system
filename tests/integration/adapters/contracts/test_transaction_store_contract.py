"""Contract every ``TransactionStore`` adapter must honour, run against the memory store.

What: one reusable check, ``check_transaction_store_contract``, and tests proving that it passes for
the memory store and fails for a deliberately broken store.

When: run by pytest with the integration suite.

Why: makes the guarantees in contracts/ports.md executable, so any future store can prove itself.
"""

import unittest

from rescue.adapters.memory import MemoryTransactionStore
from tests.integration.adapters.contracts.checks.transaction_store import (
    check_transaction_store_contract,
)
from tests.integration.adapters.contracts.doubles.publishes_on_exception import (
    PublishesOnException,
)


class TransactionStoreContractTests(unittest.TestCase):
    """Runs the transaction-store contract against the memory store and against a seeded broken store.

    What: three tests: the memory store passes, the broken store fails, the memory store rejects a
    wrong initial state.

    When: run by pytest with the integration suite.

    Why: proves the contract is both satisfied by a real store and enforceable against a faulty one.
    """

    def test_memory_store_honours_the_contract(self):
        """Check that the in-memory store passes the transaction-store contract.

        What: runs ``check_transaction_store_contract`` against ``MemoryTransactionStore``.

        When: run by pytest on every ``make test``.

        Why: the real adapter must satisfy the port it implements.
        """
        check_transaction_store_contract(MemoryTransactionStore)

    def test_contract_catches_a_store_that_publishes_on_exception(self):
        """Check that the contract fails for a store that publishes a corrupted state on error.

        What: asserts that the check raises ``AssertionError`` for ``PublishesOnException``.

        When: run by pytest on every ``make test``.

        Why: a seeded broken store proves the contract can actually fail.
        """
        with self.assertRaises(AssertionError):
            check_transaction_store_contract(PublishesOnException)

    def test_memory_store_rejects_an_initial_state_that_is_not_a_run_state(self):
        """Check that the memory store refuses an initial state of the wrong type.

        What: asserts that constructing ``MemoryTransactionStore`` with a string raises ``TypeError``.

        When: run by pytest on every ``make test``.

        Why: a store that starts from invalid state would break every later transaction.
        """
        with self.assertRaises(TypeError):
            MemoryTransactionStore("not a state")


if __name__ == "__main__":
    unittest.main()
