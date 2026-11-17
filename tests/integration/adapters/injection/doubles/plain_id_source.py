"""Plain ID source double that does not inherit the ``IdSource`` port and records the kinds it is asked for.

What: one class, ``PlainIdSource``, that only has the ``next_id`` method the port requires.

When: imported only by ``test_injection.py``.

Why: proves the composition root accepts an ID source without nominal inheritance from the port.
"""


class PlainIdSource:
    """An ID source that is not an ``IdSource`` subclass and records the kinds it is asked for.

    What: returns ``<kind>-plain`` and keeps the list of kinds requested.

    When: passed to ``new_run`` by the injection test.

    Why: proves the composition root does not require nominal inheritance from the port.
    """

    def __init__(self) -> None:
        """Start with no kinds recorded.

        What: creates an empty list of requested kinds.

        When: called once by the test before the run is built.

        Why: the test can check which source handed out which IDs.
        """
        self.kinds: list[str] = []

    def next_id(self, kind: str) -> str:
        """Record ``kind`` and return a fixed-shape ID.

        What: appends ``kind`` to ``kinds`` and returns ``<kind>-plain``.

        When: called by the central or the experiment runner whenever they draw an ID.

        Why: the record lets the test prove that the injected source was the one used.
        """
        self.kinds.append(kind)
        return f"{kind}-plain"
