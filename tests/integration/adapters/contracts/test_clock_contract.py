"""Contract every ``Clock`` adapter must honour, run against the zero clock.

What: one reusable check, ``check_clock_contract``, and tests proving that it passes for the zero
clock and fails for a clock that returns a negative instant.

When: run by pytest with the integration suite.

Why: makes the clock guarantee (CL-1, CL-2 in contracts/ports.md) executable for any future clock.
"""

import unittest
from decimal import Decimal

from rescue.adapters.memory import ZeroClock
from tests.integration.adapters.contracts.checks.clock import check_clock_contract
from tests.integration.adapters.contracts.doubles.negative_clock import NegativeClock


class ClockContractTests(unittest.TestCase):
    """Runs the clock contract against the zero clock and against a seeded broken clock.

    What: three tests: the zero clock passes, the broken clock fails, the zero clock always answers
    the same instant.

    When: run by pytest with the integration suite.

    Why: proves the contract is satisfied by a real clock and enforceable against a faulty one.
    """

    def test_zero_clock_honours_the_contract(self):
        """Check that the zero clock passes the clock contract.

        What: runs ``check_clock_contract`` against ``ZeroClock``.

        When: run by pytest on every ``make test``.

        Why: the real adapter must return a valid instant.
        """
        check_clock_contract(ZeroClock)

    def test_contract_catches_a_clock_that_returns_an_invalid_instant(self):
        """Check that the contract fails for a clock that returns a negative instant.

        What: asserts that the check raises ``AssertionError`` for ``NegativeClock``.

        When: run by pytest on every ``make test``.

        Why: a seeded broken clock proves the contract can actually fail.
        """
        with self.assertRaises(AssertionError):
            check_clock_contract(NegativeClock)

    def test_zero_clock_always_returns_the_same_instant(self):
        """Check that repeated reads of the zero clock always give instant zero.

        What: reads the clock five times and asserts that every read is ``0``.

        When: run by pytest on every ``make test``.

        Why: the demo output and the tests depend on a frozen clock.
        """
        clock = ZeroClock()
        self.assertEqual({clock.now() for _ in range(5)}, {Decimal("0")})


if __name__ == "__main__":
    unittest.main()
