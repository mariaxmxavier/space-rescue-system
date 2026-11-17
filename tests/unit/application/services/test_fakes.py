"""Tests of the shared application test fakes.

What: proves the fakes publish, count and record as the service tests rely on.
When called: by pytest with the rest of the application unit tests.
Why: a wrong fake would hide a wrong service, so the fakes are checked once here.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

import dataclasses
import unittest

from tests.unit.application.services.fakes import FakeIds, FakeSimulator, FakeStore, empty_state


class FakeStoreTests(unittest.TestCase):
    def test_publishes_the_new_state_and_returns_the_result(self):
        store = FakeStore(empty_state())
        changed = dataclasses.replace(store.snapshot(), central_id="central-2")

        result = store.transact(lambda state: (changed, "done"))

        self.assertEqual("done", result)
        self.assertEqual(changed, store.snapshot())

    def test_publishes_nothing_when_the_operation_raises(self):
        store = FakeStore(empty_state())

        def fail(state):
            raise ValueError("refused")

        with self.assertRaises(ValueError):
            store.transact(fail)

        self.assertEqual(empty_state(), store.snapshot())


class FakeIdsTests(unittest.TestCase):
    def test_counts_each_kind_separately(self):
        ids = FakeIds()

        drawn = [ids.next_id("request"), ids.next_id("event"), ids.next_id("request")]

        self.assertEqual(["request-1", "event-1", "request-2"], drawn)


class FakeSimulatorTests(unittest.TestCase):
    def test_records_calls_and_returns_preset_snapshots_in_order(self):
        simulator = FakeSimulator(["first", "second"])

        first = simulator.simulate("scenario", "policy", "sim-1")
        second = simulator.simulate("scenario-2", "policy-2", "sim-2")

        self.assertEqual(["first", "second"], [first, second])
        self.assertEqual(
            [("scenario", "policy", "sim-1"), ("scenario-2", "policy-2", "sim-2")],
            simulator.calls,
        )
