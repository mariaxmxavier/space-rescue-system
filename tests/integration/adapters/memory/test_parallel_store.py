"""Parallel requests against the in-memory store, as an API that receives them at the same time.

What: many threads submit transactions to one store at once, and the real central registers many
missions at once; the tests then check the published state.

When: run by pytest with the integration suite.

Why: the store must process simultaneous requests in parallel without losing an update, and the
tests must show that the requests really overlapped, not that they happened to run one by one.
"""

import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier, Lock

from rescue.adapters.memory import MemoryTransactionStore
from rescue.application.contracts import RegisterMission
from rescue.application.state import RunState
from rescue.bootstrap import new_run
from rescue.market.models.b3_market import B3Market

REQUESTS = 40
MISSIONS = 20


def initial_state() -> RunState:
    """Build the empty run state the parallel requests start from.

    What: a ``RunState`` with fixed identities and an empty market.

    When: called once per test, before the store is built.

    Why: the same starting state keeps the tests independent of one another.
    """
    return RunState(
        application_run_id="RUN-1",
        central_id="CENTRAL-1",
        market=B3Market(market_id="MARKET-RUN-1"),
    )


class ParallelStoreTests(unittest.TestCase):
    """Simultaneous transactions and registrations through the store and the central.

    What: three tests: concurrent commits lose nothing, read-only transactions never publish, and
    concurrent central registrations all succeed.

    When: run by pytest with the integration suite.

    Why: proves the store is parallel and still consistent under real contention.
    """

    def test_simultaneous_commits_lose_no_update_and_really_overlap(self):
        """Check that every concurrent commit is published once and that some of them conflicted.

        What: starts REQUESTS threads; each first attempt waits until every thread holds the same
        snapshot, so all but one commit conflict and retry. Each thread appends its own command
        index. Then it checks that all appends are present exactly once, and that the operations ran
        more times than there were requests, which only happens when retries occurred.

        When: run by pytest on every ``make test``.

        Why: a lost update would drop a request, and no retry would mean the requests ran one at a
        time, so the test would prove nothing about parallel safety.
        """
        store = MemoryTransactionStore(initial_state())
        every_snapshot_taken = Barrier(REQUESTS)
        attempts = []
        attempts_guard = Lock()

        def submit(index: int) -> None:
            first_attempt = [True]

            def operation(state: RunState):
                with attempts_guard:
                    attempts.append(index)
                if first_attempt[0]:
                    first_attempt[0] = False
                    every_snapshot_taken.wait(timeout=10)
                return replace(state, command_index=state.command_index + (f"req-{index}",)), None

            store.transact(operation)

        with ThreadPoolExecutor(max_workers=REQUESTS) as pool:
            list(pool.map(submit, range(REQUESTS)))

        published = store.transact(lambda state: (state, state.command_index))
        self.assertEqual(sorted(published), sorted(f"req-{index}" for index in range(REQUESTS)))
        self.assertGreater(len(attempts), REQUESTS)

    def test_read_only_transactions_never_publish_or_retry(self):
        """Check that simultaneous reads run once each and leave the published state untouched.

        What: starts REQUESTS threads that each read the state; then checks that every read ran
        exactly once and that the published state is the one that was there before.

        When: run by pytest on every ``make test``.

        Why: a read that published would bump the version and force writers to retry; reads must be
        free.
        """
        store = MemoryTransactionStore(initial_state())
        before = store.snapshot()
        barrier = Barrier(REQUESTS)
        runs = []
        runs_guard = Lock()

        def read(index: int) -> RunState:
            barrier.wait(timeout=10)

            def operation(state: RunState):
                with runs_guard:
                    runs.append(index)
                return state, state

            return store.transact(operation)

        with ThreadPoolExecutor(max_workers=REQUESTS) as pool:
            reads = list(pool.map(read, range(REQUESTS)))

        self.assertEqual(len(runs), REQUESTS)
        self.assertTrue(all(state is before for state in reads))
        self.assertIs(store.snapshot(), before)

    def test_simultaneous_registrations_through_the_central_all_succeed(self):
        """Check that many missions registered at the same time are all published and queryable.

        What: sends MISSIONS registrations to one central from parallel threads, then checks each
        result is applied and that every mission can be read back with no history.

        When: run by pytest on every ``make test``.

        Why: the real use case must work under parallel requests, not only the store in isolation.
        """
        central = new_run("RUN-1", "CENTRAL-1").central
        mission_ids = [f"MISSION-{index}" for index in range(MISSIONS)]

        def register(mission_id: str):
            return central.register_mission(
                RegisterMission(
                    mission_id=mission_id,
                    station_name=f"Station {mission_id}",
                    people_count=3,
                    created_at=0,
                )
            )

        with ThreadPoolExecutor(max_workers=MISSIONS) as pool:
            results = list(pool.map(register, mission_ids))

        self.assertTrue(all(result.status == "applied" for result in results))
        for mission_id in mission_ids:
            self.assertEqual(central.get_history(mission_id).value, ())


if __name__ == "__main__":
    unittest.main()
