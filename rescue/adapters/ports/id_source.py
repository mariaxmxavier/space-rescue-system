"""The ``IdSource`` port: where the application gets new identifiers.

What: declares a source of IDs that are unique within one run.

When: ``RescueCentral`` and the experiment runner ask it for an ID whenever they create a request,
event, message, command or other record.

Why: the rules need unique IDs but must not care how they are made.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from rescue.values import Id


class IdSource(ABC):
    """Source of run-unique identifiers.

    What: hands out a fresh ID for a given kind of thing.

    When: built once per run by ``rescue.bootstrap.new_run``, or supplied by the caller.

    Why: ID generation is an outside-world detail (sequence, UUID, database key); a port keeps
    the rules free of it.
    """

    @abstractmethod
    def next_id(self, kind: str) -> Id:
        """Return an ID never returned before in this run.

        What: a new ``Id`` for ``kind`` (e.g. ``"request"``).

        When: called each time a use case creates something that needs an identity.

        Why: two things in one run must never share an ID.
        """
