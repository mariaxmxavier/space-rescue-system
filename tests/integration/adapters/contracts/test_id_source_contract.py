"""Contract every ``IdSource`` adapter must honour, run against the sequence source.

What: one reusable check, ``check_id_source_contract``, and tests proving that it passes for the
sequence source and fails for a source that repeats IDs.

When: run by pytest with the integration suite.

Why: makes the ID guarantee (ID-1, ID-2 in contracts/ports.md) executable for any future source.
"""

import unittest

from rescue.adapters.memory import SequenceIdSource
from tests.integration.adapters.contracts.checks.id_source import check_id_source_contract
from tests.integration.adapters.contracts.doubles.repeats_ids import RepeatsIds


class IdSourceContractTests(unittest.TestCase):
    """Runs the ID-source contract against the sequence source and against a seeded repeating source.

    What: three tests: the sequence source passes, the repeating source fails, reserved IDs are
    skipped.

    When: run by pytest with the integration suite.

    Why: proves the contract is satisfied by a real source and enforceable against a faulty one.
    """

    def test_sequence_source_honours_the_contract(self):
        """Check that the sequence source passes the ID-source contract.

        What: runs ``check_id_source_contract`` against ``SequenceIdSource``.

        When: run by pytest on every ``make test``.

        Why: the real adapter must never repeat an ID within a run.
        """
        check_id_source_contract(SequenceIdSource)

    def test_contract_catches_a_source_that_repeats_ids(self):
        """Check that the contract fails for a source that repeats IDs.

        What: asserts that the check raises ``AssertionError`` for ``RepeatsIds``.

        When: run by pytest on every ``make test``.

        Why: a seeded repeating source proves the contract can actually fail.
        """
        with self.assertRaises(AssertionError):
            check_id_source_contract(RepeatsIds)

    def test_sequence_source_skips_reserved_ids(self):
        """Check that a reserved ID is never handed out again.

        What: reserves ``request-00000001`` and asserts the next request ID is ``request-00000002``.

        When: run by pytest on every ``make test``.

        Why: a run seeded with values cloned from another run must not clash with them.
        """
        source = SequenceIdSource(("request-00000001",))
        self.assertEqual(source.next_id("request"), "request-00000002")


if __name__ == "__main__":
    unittest.main()
