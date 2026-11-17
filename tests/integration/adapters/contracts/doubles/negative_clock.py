"""Seeded broken ``Clock`` double that answers a negative instant.

What: one class, ``NegativeClock``, used as the broken clock in the clock contract.

When: imported only by ``test_clock_contract.py``.

Why: a contract check that cannot fail proves nothing; this double shows the check catches a clock
that returns an invalid instant.
"""

from decimal import Decimal

from rescue.adapters.ports import Clock


class NegativeClock(Clock):
    """A deliberately broken clock that answers a negative instant.

    What: returns ``-1`` on every call.

    When: used only by the test proving that the contract check fails on a broken clock.

    Why: the seeded fault the clock contract must catch.
    """

    def now(self) -> Decimal:
        """Return a negative instant.

        What: ``Decimal("-1")``.

        When: called by the contract check in place of a real clock.

        Why: the seeded fault the contract must catch.
        """
        return Decimal("-1")
