"""Atomic publication behavior for the in-memory run store.

What: tests for the behaviour only the memory store has beyond the port contract: concurrent reads,
and the immutability of ``RunState`` registry values.

When: run by pytest with the integration suite.

Why: the port contract is checked in ``tests/integration/adapters/contracts``; this file covers what
the in-memory implementation adds on top of it.
"""

import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

from rescue.adapters.memory import MemoryTransactionStore
from rescue.application.state import RunState
from rescue.market.models.b3_market import B3Market
from rescue.market.models.fleet import Ship
from rescue.mission.models import MissionData
from rescue.mission.rules import register


def initial_state():
    """Build the empty run state these tests start from.

    What: a ``RunState`` with fixed identities and an empty market.

    When: called once per test, before the store is built.

    Why: the same starting state keeps each test independent.
    """
    return RunState(
        application_run_id="RUN-1",
        central_id="CENTRAL-1",
        market=B3Market(market_id="MARKET-RUN-1"),
    )


class MemoryTransactionStoreTests(unittest.TestCase):
    """Tests for the in-memory store's own behaviour.

    What: success publication, immutability of registry values, discarding of staged state, and a
    concurrent read during a write.

    When: run by pytest with the integration suite.

    Why: covers what the port contract does not: the lock and the immutable state it relies on.
    """

    def test_success_publishes_new_immutable_state(self):
        """Check that a successful transaction publishes the new state and leaves the old one intact.

        What: runs an operation that adds a command index, then checks the returned result, the
        published state and that the original state object is unchanged.

        When: run by pytest on every ``make test``.

        Why: the published state must be the staged one, and earlier snapshots must not change.
        """
        original = initial_state()
        store = MemoryTransactionStore(original)

        returned = store.transact(
            lambda state: (replace(state, command_index=("accepted",)), "done")
        )

        self.assertEqual(returned, "done")
        self.assertEqual(store.transact(lambda state: (state, state.command_index)), ("accepted",))
        self.assertEqual(original.command_index, ())

    def test_run_state_rejects_mutable_registry_values(self):
        """Check that ``RunState`` refuses mutable values in its registry fields.

        What: replaces ``policies`` with a dict and asserts that ``ValueError`` is raised.

        When: run by pytest on every ``make test``.

        Why: an immutable state is what makes atomic publication safe.
        """
        with self.assertRaises(ValueError):
            replace(initial_state(), policies=({"mutable": []},))

    def test_exception_discards_staged_state(self):
        """Check that a staged change is discarded when its operation raises.

        What: stages a command index, raises, then checks the published state is still empty.

        When: run by pytest on every ``make test``.

        Why: a failed use case must leave no partial change behind.
        """
        original = initial_state()
        store = MemoryTransactionStore(original)

        def fail_after_staging(state):
            staged = replace(state, command_index=("must-not-publish",))
            self.assertEqual(staged.command_index, ("must-not-publish",))
            raise RuntimeError("abort")

        with self.assertRaisesRegex(RuntimeError, "abort"):
            store.transact(fail_after_staging)

        self.assertEqual(store.transact(lambda state: (state, state.command_index)), ())

    def test_concurrent_read_observes_one_complete_published_snapshot(self):
        """Check that a read during a write sees the state before or after the write, never half of it.

        What: starts a write and a read at the same moment and asserts the read observes either no
        ship and no mission, or one of each.

        When: run by pytest on every ``make test``.

        Why: the reader must never see a half-applied change, which is the store's core promise.
        """
        store = MemoryTransactionStore(initial_state())
        barrier = Barrier(3)

        def write_registration():
            barrier.wait(timeout=5)

            def operation(state):
                updated = replace(
                    state,
                    market=replace(state.market, ships=(Ship("SHIP-1", "Rescue One"),)),
                    missions=(register(MissionData("MISSION-1", "Station One", 4, 0)),),
                )
                return updated, None

            store.transact(operation)

        def read_snapshot():
            barrier.wait(timeout=5)
            return store.transact(
                lambda state: (state, (len(state.market.ships), len(state.missions)))
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            writer = executor.submit(write_registration)
            reader = executor.submit(read_snapshot)
            barrier.wait(timeout=5)
            writer.result(timeout=5)
            observed = reader.result(timeout=5)

        self.assertIn(observed, ((0, 0), (1, 1)))


if __name__ == "__main__":
    unittest.main()
