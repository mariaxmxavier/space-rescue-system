"""Sequential ``IdSource`` that skips reserved IDs.

What: makes IDs of the form ``<kind>-00000001`` from one counter per run.

When: used by ``rescue.bootstrap.new_run`` when the caller supplies no ID source.

Why: readable, deterministic IDs make the demo and tests reproducible; skipping reserved IDs
lets a run be seeded with values cloned from another run without clashes.
"""

from __future__ import annotations

from threading import Lock

from rescue.adapters.ports.id_source import IdSource
from rescue.values import Id, normalize_id


class SequenceIdSource(IdSource):
    """Thread-safe counter that hands out run-unique IDs.

    What: implements ``IdSource`` with a shared counter and a set of taken IDs.

    When: one instance per run, unless the caller injects another source.

    Why: a lock keeps IDs unique even when use cases run on several threads.
    """

    def __init__(self, reserved_ids: tuple[Id, ...] = ()) -> None:
        """Start the counter at zero and mark ``reserved_ids`` as taken.

        What: stores the reserved IDs and creates the lock.

        When: called once by ``rescue.bootstrap.new_run``.

        Why: IDs already present in the run must never be handed out again.
        """
        self._lock = Lock()
        self._counter = 0
        self._reserved_ids = set(reserved_ids)

    def next_id(self, kind: str) -> Id:
        """Return the next free ``<kind>-<counter>`` ID.

        What: increments the counter until the candidate is not taken, then reserves it.

        When: called by ``RescueCentral`` and the experiment runner each time they create something
        that needs an identity.

        Why: one counter per run gives every ID a distinct number in creation order, whatever its
        kind, and one lock makes the draw and the reservation a single step.
        """
        normalized_kind = normalize_id(kind)
        with self._lock:
            while True:
                self._counter += 1
                candidate = f"{normalized_kind}-{self._counter:08d}"
                if candidate not in self._reserved_ids:
                    self._reserved_ids.add(candidate)
                    return candidate
