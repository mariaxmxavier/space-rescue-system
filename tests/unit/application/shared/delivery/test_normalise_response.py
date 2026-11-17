"""normalise_response tests."""

import unittest

from rescue.application.shared.delivery.normalise_response import normalise_response
from rescue.values import DomainValidationError
from tests.unit.application.shared.delivery.support import response


class NormaliseResponseTests(unittest.TestCase):
    """normalise_response turns a command into checked fields and a message.

    What: normalises ids, attempt, instants and seats and builds the CommunicationMessage.
    When called: by tests of the first delivery step.
    Why: later steps read only valid values.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def test_builds_the_ship_response_message(self):
        normalised = normalise_response(response())
        self.assertEqual(normalised.message.kind, "ship_response")
        self.assertEqual(normalised.message.request_id, "request-1")
        self.assertEqual(normalised.confirmed, 3)
        self.assertEqual(normalised.received_at, normalised.sent_at + 1)

    def test_a_lost_delivery_has_no_receipt(self):
        self.assertIsNone(normalise_response(response(received_at=None)).received_at)

    def test_receipt_before_send_is_rejected(self):
        with self.assertRaisesRegex(DomainValidationError, "receipt cannot precede send time"):
            normalise_response(response(sent_at="5", received_at="4"))
