"""Reusable clock contract check.

What: ``check_clock_contract``.

When: imported by the contract tests of every ``Clock`` adapter.

Why: one shared check lets a future clock prove itself without copying the guarantee (FR-005).
"""

from collections.abc import Callable
from decimal import Decimal

from rescue.adapters.ports import Clock


def check_clock_contract(make_clock: Callable[[], Clock]) -> None:
    """Raise ``AssertionError`` if the clock returns something other than a valid instant.

    What: reads one instant and asserts it is a finite ``Decimal`` that is not negative.

    When: called by the tests that prove the zero clock conforms and that a broken clock is caught.

    Why: a valid instant is the clock guarantee CL-1 in contracts/ports.md.
    """
    instant = make_clock().now()
    assert isinstance(instant, Decimal)
    assert instant.is_finite()
    assert instant >= 0
