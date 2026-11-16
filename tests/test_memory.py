"""Atomic publication behavior for the in-memory run store."""

from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import unittest

from rescue.adapters.memory import MemoryTransactionStore
from rescue.application.state import RunState
from rescue.market.models import B3Market
from rescue.market.models import Ship
from rescue.mission.models import MissionData
from rescue.mission.rules import register


def initial_state():
    return RunState(
        application_run_id="RUN-1",
        central_id="CENTRAL-1",
        market=B3Market(market_id="MARKET-RUN-1"),
    )


class MemoryTransactionStoreTests(unittest.TestCase):
    def test_success_publishes_new_immutable_state(self):
        original = initial_state()
        store = MemoryTransactionStore(original)

        returned = store.transact(
            lambda state: (replace(state, command_index=("accepted",)), "done")
        )

        self.assertEqual(returned, "done")
        self.assertEqual(store.transact(lambda state: (state, state.command_index)), ("accepted",))
        self.assertEqual(original.command_index, ())

    def test_run_state_rejects_mutable_registry_values(self):
        with self.assertRaises(ValueError):
            replace(initial_state(), policies=({"mutable": []},))

    def test_exception_discards_staged_state(self):
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
