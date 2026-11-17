"""The ``Clock`` port: where the application gets the time.

What: declares a source of the current instant.

When: held by ``RescueCentral`` and ``RunContext`` once ``rescue.bootstrap.new_run`` builds them.

Why: rules must not read the wall clock, so runs stay deterministic and testable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from rescue.values import Instant


class Clock(ABC):
    """Source of operation time.

    What: answers "what time is it now" for one run.

    When: built once per run by ``rescue.bootstrap.new_run``, or supplied by the caller.

    Why: time is an outside-world detail; hiding it behind a port lets tests and simulations
    control it.
    """

    @abstractmethod
    def now(self) -> Instant:
        """Return the current instant.

        What: a non-negative ``Instant`` for the run's timeline.

        When: called only by a use case that needs a timestamp the caller did not supply; none does
        today, because every timed command carries an explicit instant.

        Why: one place decides what "now" means, so every timestamp in a run agrees.
        """
