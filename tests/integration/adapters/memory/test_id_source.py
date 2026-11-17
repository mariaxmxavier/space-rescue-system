"""Concurrency test for ``SequenceIdSource``.

What: draws IDs from one source on several threads at once and checks they are all distinct.

When: runs with the integration tests, against the real in-memory adapter.

Why: the source guards its counter with a lock, and a mechanism that exists for concurrency must
be tested under concurrency.
"""

from __future__ import annotations

import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from rescue.adapters.memory import SequenceIdSource

THREADS = 8
DRAWS_PER_THREAD = 50
SWITCH_INTERVAL = 1e-6


class SequenceIdSourceConcurrencyTests(unittest.TestCase):
    """Threaded draws from one ``SequenceIdSource``.

    What: starts every thread together and collects what each one drew.

    When: one test per concurrency property of the source.

    Why: a missing lock could let two threads draw the same ID when they interleave inside ``next_id``;
    this test exercises that risk but is not a guaranteed detector.
    """

    def test_threads_drawing_together_never_receive_the_same_id(self) -> None:
        """Every ID drawn across all threads is unique.

        What: 8 threads of 50 draws start behind a barrier and share one source.

        When: the thread switch interval is shortened to make interleaving more likely, then restored.

        Why: duplicate IDs would make two records collide in the store.
        """
        source = SequenceIdSource()
        barrier = Barrier(THREADS)

        def draw() -> list[str]:
            barrier.wait()
            return [source.next_id("request") for _ in range(DRAWS_PER_THREAD)]

        previous_interval = sys.getswitchinterval()
        sys.setswitchinterval(SWITCH_INTERVAL)
        try:
            with ThreadPoolExecutor(max_workers=THREADS) as pool:
                futures = [pool.submit(draw) for _ in range(THREADS)]
                drawn = [id_ for future in futures for id_ in future.result()]
        finally:
            sys.setswitchinterval(previous_interval)

        self.assertEqual(len(drawn), THREADS * DRAWS_PER_THREAD)
        self.assertEqual(len(set(drawn)), len(drawn))


if __name__ == "__main__":
    unittest.main()
