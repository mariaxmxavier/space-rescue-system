"""classify_response tests."""

import unittest

from rescue.application.shared.delivery.classify_response import classify_response
from rescue.application.shared.delivery.normalise_response import normalise_response
from rescue.application.shared.delivery.publish_delivery import publish_delivery
from tests.unit.application.shared.delivery.support import response, state_with_request


class ClassifyResponseTests(unittest.TestCase):
    """classify_response gathers the delivery facts and asks for the decision.

    What: looks up delivery, message, mission and request, then classifies.
    When called: by tests of the second delivery step.
    Why: the decision and the context it was made from travel together.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def test_a_new_delivery_for_an_open_request_is_applied(self):
        context, decision = classify_response(state_with_request(), normalise_response(response()))
        self.assertEqual(decision.action, "apply")
        self.assertEqual(context.request.request_id, "request-1")
        self.assertEqual(context.mission.mission_id, "mission-1")
        self.assertIsNone(context.known_delivery)
        self.assertFalse(context.message_conflicts)

    def test_a_repeated_identical_delivery_is_a_duplicate(self):
        state = state_with_request()
        normalised = normalise_response(response())
        context, _ = classify_response(state, normalised)
        state = publish_delivery(state, context, "applied", "response_applied", report=False)
        repeat_context, decision = classify_response(state, normalised)
        self.assertEqual(decision.action, "none")
        self.assertEqual(decision.result_status, "ignored")
        self.assertIsNotNone(repeat_context.known_delivery)

    def test_a_different_message_under_a_known_id_conflicts(self):
        state = state_with_request()
        context, _ = classify_response(state, normalise_response(response()))
        state = publish_delivery(state, context, "applied", "response_applied", report=False)
        other = normalise_response(response(delivery_id="delivery-2", confirmed_seats=1))
        context, decision = classify_response(state, other)
        self.assertTrue(context.message_conflicts)
        self.assertEqual(decision.result_reason, "identity_conflict")
