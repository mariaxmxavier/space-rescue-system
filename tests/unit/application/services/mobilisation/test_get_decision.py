import unittest

from rescue.application.contracts import Mobilise
from rescue.application.services.mobilisation.get_decision import get_decision
from rescue.application.services.mobilisation.mobilise import mobilise
from tests.unit.application.services.fakes import FakeIds
from tests.unit.application.services.mobilisation.support import seeded_store


class GetDecisionTests(unittest.TestCase):
    def test_returns_the_recorded_decision(self):
        store = seeded_store()
        decision = mobilise(
            Mobilise("MISSION-1", "EARLIEST", 1, 1), store=store, id_source=FakeIds()
        ).value

        result = get_decision(decision.decision_id, store=store)

        self.assertEqual((result.status, result.value), ("applied", decision))

    def test_unknown_decision_is_rejected(self):
        result = get_decision("missing", store=seeded_store())

        self.assertEqual((result.status, result.reason), ("rejected", "unknown_decision"))

    def test_blank_id_is_rejected_as_invalid_input(self):
        result = get_decision("  ", store=seeded_store())

        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))
