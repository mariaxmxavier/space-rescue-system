"""Fixed ``Clock`` that always answers zero.

What: a clock frozen at instant ``0``.

When: used by ``rescue.bootstrap.new_run`` when the caller supplies no clock.

Why: callers pass explicit times for every timed step, so the fallback only needs to be
deterministic; a frozen clock makes every run reproducible.
"""

from __future__ import annotations

from decimal import Decimal

from rescue.adapters.ports.clock import Clock
from rescue.values import Instant


class ZeroClock(Clock):
    """A ``Clock`` that never moves.

    What: implements ``Clock`` with a constant instant.

    When: one instance per run, unless the caller injects another clock.

    Why: simulated time is enough for this system; real time would make runs differ.
    """

    def now(self) -> Instant:
        """Return instant ``0``.

        What: always ``Decimal("0")``.

        When: called only if a use case needs a time the caller did not give; none does today.

        Why: a constant keeps the demo output and tests identical on every run.
        """
        return Decimal("0")
