"""install_baseline copies the baseline into a fresh run store under the new run id."""

import unittest
from dataclasses import dataclass
from types import SimpleNamespace

from rescue.experiments.simulation.install_baseline import install_baseline


@dataclass(frozen=True)
class State:
    market: object = None
    missions: tuple = ()
    command_index: tuple = ()
    message_index: tuple = ()
    delivery_index: tuple = ()
    decision_index: tuple = ()


@dataclass(frozen=True)
class Market:
    market_id: str


class FakeStore:
    def __init__(self) -> None:
        self.state = State()

    def transact(self, operation):
        self.state, result = operation(self.state)
        return result


class InstallBaselineTests(unittest.TestCase):
    def test_five_item_command_entries_get_the_new_run_id(self) -> None:
        store = FakeStore()
        baseline = SimpleNamespace(
            market=Market("old"),
            missions=("m1",),
            command_index=(("old-run", "c1", "a", "b", "c"), ("x", "y"), "raw"),
            message_index=("msg",),
            delivery_index=("del",),
            decision_index=("dec",),
        )
        install_baseline(SimpleNamespace(store=store), baseline, "run-2")
        self.assertEqual(
            store.state.command_index, (("run-2", "c1", "a", "b", "c"), ("x", "y"), "raw")
        )
        self.assertEqual(store.state.market.market_id, "run-2-market")
        self.assertEqual(store.state.missions, ("m1",))
        self.assertEqual(store.state.message_index, ("msg",))
        self.assertEqual(store.state.delivery_index, ("del",))
        self.assertEqual(store.state.decision_index, ("dec",))


if __name__ == "__main__":
    unittest.main()
