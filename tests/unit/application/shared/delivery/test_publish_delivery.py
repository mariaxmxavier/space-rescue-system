"""publish_delivery tests."""

import unittest

from rescue.application.shared.delivery.classify_response import classify_response
from rescue.application.shared.delivery.normalise_response import normalise_response
from rescue.application.shared.delivery.publish_delivery import publish_delivery
from rescue.application.shared.delivery.resolve_session import resolve_session
from tests.unit.application.shared.delivery.support import response, state_with_request


def context_for(command):
    state = state_with_request()
    context, _ = classify_response(state, normalise_response(command))
    return state, context


class PublishDeliveryTests(unittest.TestCase):
    """publish_delivery writes the delivery indices and the decision report.

    What: appends the delivery and message, and issues a report when a session exists.
    When called: by tests of the last delivery step.
    Why: one write path keeps indices, session and reports aligned.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def test_a_received_delivery_with_a_session_issues_a_report(self):
        command = response()
        state, context = context_for(command)
        context, _ = resolve_session(state, context, command)
        published = publish_delivery(state, context, "applied", "response_applied")
        self.assertEqual(len(published.delivery_index), 1)
        self.assertEqual(len(published.message_index), 1)
        self.assertEqual(len(published.session_index[0].reports), 1)
        self.assertEqual(published.session_index[0].reports[0].report_id, "report-delivery-1")

    def test_report_false_records_the_delivery_without_a_report(self):
        command = response()
        state, context = context_for(command)
        context, _ = resolve_session(state, context, command)
        published = publish_delivery(state, context, "ignored", "duplicate_sequence", report=False)
        self.assertEqual(len(published.delivery_index), 1)
        self.assertEqual(published.session_index, ())

    def test_a_lost_delivery_has_no_session_and_no_report(self):
        state, context = context_for(response(received_at=None))
        published = publish_delivery(state, context, "lost", "transport_loss")
        self.assertEqual(len(published.delivery_index), 1)
        self.assertEqual(published.session_index, ())

    def test_keep_message_false_leaves_the_message_index_alone(self):
        state, context = context_for(response())
        published = publish_delivery(
            state, context, "rejected", "identity_conflict", keep_message=False
        )
        self.assertEqual(published.message_index, ())
        self.assertEqual(len(published.delivery_index), 1)
