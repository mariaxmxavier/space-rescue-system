"""Plain clock double that does not inherit the ``Clock`` port.

What: one class, ``PlainClock``, that only has the ``now`` method the port requires.

When: imported only by ``test_injection.py``.

Why: proves the composition root accepts a clock without nominal inheritance from the port.
"""

from decimal import Decimal


class PlainClock:
    """A clock that is not a ``Clock`` subclass.

    What: answers a fixed instant of ``7``.

    When: passed to ``new_run`` by the injection test.

    Why: proves the composition root does not require nominal inheritance from the port.
    """

    def now(self) -> Decimal:
        """Return the fixed instant ``7``.

        What: ``Decimal("7")``.

        When: called only if a use case reads the clock; none does today.

        Why: a stable value makes the test's expectation explicit.
        """
        return Decimal("7")
