"""MessageDelivery model tests."""

import inspect
import unittest
from decimal import Decimal

from rescue.communication.models.deliveries.message_delivery import MessageDelivery
from rescue.communication.models.sessions.session_envelope import SessionEnvelope
from rescue.communication.models.vocabulary.delivery_disposition import DeliveryDisposition
from rescue.communication.models.vocabulary.delivery_reason import DeliveryReason
from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from rescue.values import DomainValidationError


def make(**overrides):
    fields = {
        "delivery_id": "d1",
        "attempt_number": 1,
        "received_at": 5,
        "disposition": "applied",
        "reason": "response_applied",
    }
    return MessageDelivery(**{**fields, **overrides})


def session_envelope(**overrides):
    fields = {
        "session_id": "local:ship-1",
        "version": 1,
        "direction": FlowDirection.INBOUND,
        "sequence": 1,
    }
    return SessionEnvelope(**(fields | overrides))


class MessageDeliveryTests(unittest.TestCase):
    def test_string_values_become_vocabulary_members(self):
        delivery = make()
        self.assertIs(delivery.disposition, DeliveryDisposition.APPLIED)
        self.assertIs(delivery.reason, DeliveryReason.RESPONSE_APPLIED)
        self.assertEqual(delivery.received_at, Decimal(5))

    def test_enum_members_are_accepted(self):
        delivery = make(
            disposition=DeliveryDisposition.LATE, reason=DeliveryReason.DEADLINE_EXPIRED
        )
        self.assertIs(delivery.disposition, DeliveryDisposition.LATE)

    def test_unknown_disposition_is_rejected(self):
        with self.assertRaises(DomainValidationError):
            make(disposition="bogus")

    def test_unknown_reason_is_rejected(self):
        with self.assertRaises(DomainValidationError):
            make(reason="bogus")

    def test_non_string_vocabulary_values_are_rejected(self):
        with self.assertRaises(DomainValidationError):
            make(disposition=None)
        with self.assertRaises(DomainValidationError):
            make(reason=3)

    def test_lost_delivery_has_no_receipt_time(self):
        delivery = make(disposition="lost", reason="transport_loss", received_at=None)
        self.assertIsNone(delivery.received_at)
        with self.assertRaisesRegex(
            DomainValidationError, "lost deliveries must have no receipt time"
        ):
            make(disposition="lost", reason="transport_loss", received_at=5)

    def test_received_delivery_needs_receipt_time(self):
        with self.assertRaisesRegex(
            DomainValidationError, "lost deliveries must have no receipt time"
        ):
            make(received_at=None)

    def test_lost_delivery_cannot_report_rtt(self):
        with self.assertRaisesRegex(
            DomainValidationError, "lost deliveries cannot report an observed RTT"
        ):
            make(
                disposition="lost",
                reason="transport_loss",
                received_at=None,
                communication_rtt_seconds=1,
            )

    def test_rtt_is_normalized(self):
        self.assertEqual(
            make(communication_rtt_seconds="2.5").communication_rtt_seconds, Decimal("2.5")
        )

    def test_attempt_number_must_be_positive(self):
        with self.assertRaises(DomainValidationError):
            make(attempt_number=0)

    def test_envelope_defaults_to_none(self):
        self.assertIsNone(make().envelope)

    def test_envelope_is_keyword_only(self):
        parameter = inspect.signature(MessageDelivery).parameters["envelope"]
        self.assertIs(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertIsNone(parameter.default)

    def test_inbound_envelope_is_kept(self):
        self.assertEqual(make(envelope=session_envelope()).envelope, session_envelope())

    def test_outbound_envelope_is_rejected(self):
        with self.assertRaisesRegex(DomainValidationError, "delivery envelope must be inbound"):
            make(envelope=session_envelope(direction=FlowDirection.OUTBOUND))

    def test_envelope_must_be_a_session_envelope(self):
        with self.assertRaisesRegex(
            DomainValidationError, "delivery envelope must be a session envelope"
        ):
            make(envelope="inbound")

    def test_lost_delivery_cannot_carry_envelope(self):
        with self.assertRaisesRegex(
            DomainValidationError, "lost deliveries cannot carry a session envelope"
        ):
            make(
                disposition="lost",
                reason="transport_loss",
                received_at=None,
                envelope=session_envelope(),
            )


if __name__ == "__main__":
    unittest.main()
