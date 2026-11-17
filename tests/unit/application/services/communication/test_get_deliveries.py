"""get_deliveries service tests."""

import unittest
from dataclasses import replace

from rescue.application.services.communication.get_deliveries import get_deliveries
from rescue.communication.models.deliveries.message_delivery import MessageDelivery
from rescue.communication.models.vocabulary.delivery_disposition import DeliveryDisposition
from rescue.communication.models.vocabulary.delivery_reason import DeliveryReason
from tests.unit.application.services.fakes import FakeStore, empty_state


def delivery(delivery_id):
    return MessageDelivery(
        delivery_id,
        1,
        disposition=DeliveryDisposition.LOST,
        reason=next(iter(DeliveryReason)),
    )


class GetDeliveriesTests(unittest.TestCase):
    """get_deliveries returns every attempt recorded for one message.

    What: reads the delivery index for a message id without changing the run.
    When called: by tests of the get_deliveries service.
    Why: a message with no recorded attempt is a named rejection, not an empty success.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
    """

    def setUp(self):
        self.first, self.second, self.other = delivery("d-1"), delivery("d-2"), delivery("d-3")
        index = (
            ("c-1", "message-1", self.first),
            ("c-2", "message-1", self.second),
            ("c-3", "message-2", self.other),
            "not-an-entry",
        )
        self.store = FakeStore(replace(empty_state(), delivery_index=index))

    def test_returns_the_deliveries_of_the_message_in_order(self):
        result = get_deliveries("message-1", store=self.store)
        self.assertEqual(result.status, "applied")
        self.assertEqual(result.value, (self.first, self.second))

    def test_unknown_message_is_rejected(self):
        result = get_deliveries("message-9", store=self.store)
        self.assertEqual((result.status, result.reason), ("rejected", "unknown_message"))

    def test_invalid_id_is_rejected_as_invalid_input(self):
        result = get_deliveries("", store=self.store)
        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))

    def test_nothing_is_published_on_rejection(self):
        before = self.store.state
        get_deliveries("message-9", store=self.store)
        self.assertIs(self.store.state, before)
