import unittest

from rescue.application.contracts import Mobilise
from rescue.application.services.mobilisation.mobilise import mobilise
from tests.unit.application.services.fakes import FakeIds
from tests.unit.application.services.mobilisation.support import seeded_store


class MobiliseTests(unittest.TestCase):
    def test_success_records_the_decision_and_draws_ids_in_order(self):
        store = seeded_store()
        ids = FakeIds()

        result = mobilise(Mobilise("MISSION-1", "EARLIEST", 1, 1), store=store, id_source=ids)

        self.assertEqual(result.status, "applied")
        self.assertEqual(result.value.decision_id, "decision-1")
        self.assertEqual(store.state.decision_index, (result.value,))
        self.assertEqual(ids.counts["decision"], 1)
        self.assertEqual(ids.counts["evaluation"], 1)

    def test_unknown_mission_is_rejected_and_publishes_nothing(self):
        store = seeded_store()
        before = store.state

        result = mobilise(Mobilise("MISSING", "EARLIEST", 1, 1), store=store, id_source=FakeIds())

        self.assertEqual((result.status, result.reason), ("rejected", "unknown_mission"))
        self.assertIs(store.state, before)

    def test_unknown_policy_is_rejected_and_publishes_nothing(self):
        store = seeded_store()
        before = store.state

        result = mobilise(Mobilise("MISSION-1", "OTHER", 1, 1), store=store, id_source=FakeIds())

        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))
        self.assertIs(store.state, before)

    def test_unknown_policy_revision_is_rejected(self):
        result = mobilise(
            Mobilise("MISSION-1", "EARLIEST", 2, 1), store=seeded_store(), id_source=FakeIds()
        )

        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))

    def test_invalid_input_is_rejected_and_publishes_nothing(self):
        store = seeded_store()
        before = store.state

        result = mobilise(Mobilise("MISSION-1", "EARLIEST", 0, 1), store=store, id_source=FakeIds())

        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))
        self.assertIs(store.state, before)
