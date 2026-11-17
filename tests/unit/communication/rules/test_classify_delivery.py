"""One test per precedence row of classify_delivery."""

import unittest

from rescue.communication.models.deliveries.delivery_decision import DeliveryDecision
from rescue.communication.models.deliveries.delivery_facts import DeliveryFacts
from rescue.communication.models.vocabulary.delivery_disposition import DeliveryDisposition
from rescue.communication.models.vocabulary.delivery_reason import DeliveryReason
from rescue.communication.rules.classify_delivery import classify_delivery

OPEN = {"request_known": True, "request_open": True}
CLOSED = {"request_known": True}
EXPIRED = {"request_known": True, "request_expired": True}


def facts(**overrides):
    values = {
        "delivery_known": False,
        "delivery_identical": False,
        "message_conflicts": False,
        "request_known": True,
        "request_open": False,
        "request_expired": False,
        "submitted_at": 10,
        "deadline": None,
        "sent_at": 20,
        "received_at": 30,
    }
    values.update(overrides)
    return DeliveryFacts(**values)


def decision(action, disposition, reason, status, result_reason):
    return DeliveryDecision(disposition, reason, action, status, result_reason)


class ClassifyDeliveryTest(unittest.TestCase):
    def test_row_1_known_identical_is_ignored(self):
        got = classify_delivery(facts(delivery_known=True, delivery_identical=True, **OPEN))
        self.assertEqual(got, decision("none", None, None, "ignored", None))

    def test_row_2_known_different_is_identity_conflict(self):
        got = classify_delivery(facts(delivery_known=True, **OPEN))
        self.assertEqual(got, decision("none", None, None, "rejected", "identity_conflict"))

    def test_row_4_message_conflict_is_recorded_rejected(self):
        got = classify_delivery(facts(message_conflicts=True, **OPEN))
        self.assertEqual(
            got,
            decision(
                "record",
                DeliveryDisposition.REJECTED,
                DeliveryReason.IDENTITY_CONFLICT,
                "rejected",
                "identity_conflict",
            ),
        )

    def test_row_5a_unknown_request_without_receipt_is_lost(self):
        got = classify_delivery(facts(request_known=False, received_at=None))
        self.assertEqual(
            got,
            decision(
                "record",
                DeliveryDisposition.LOST,
                DeliveryReason.TRANSPORT_LOSS,
                "applied",
                None,
            ),
        )

    def test_row_5b_unknown_request_received_is_ignored(self):
        got = classify_delivery(facts(request_known=False))
        self.assertEqual(
            got,
            decision(
                "record",
                DeliveryDisposition.IGNORED,
                DeliveryReason.UNKNOWN_REQUEST,
                "ignored",
                "unknown_request",
            ),
        )

    def test_row_6_send_before_submission_is_invalid_input(self):
        got = classify_delivery(facts(sent_at=5, **OPEN))
        self.assertEqual(
            got,
            decision(
                "record",
                DeliveryDisposition.REJECTED,
                DeliveryReason.INVALID_INPUT,
                "rejected",
                "invalid_input",
            ),
        )

    def test_row_7_no_receipt_is_lost(self):
        got = classify_delivery(facts(received_at=None, **OPEN))
        self.assertEqual(
            got,
            decision(
                "record",
                DeliveryDisposition.LOST,
                DeliveryReason.TRANSPORT_LOSS,
                "applied",
                None,
            ),
        )

    def test_row_8a_closed_expired_past_deadline_is_late(self):
        got = classify_delivery(facts(deadline=30, **EXPIRED))
        self.assertEqual(
            got,
            decision(
                "record",
                DeliveryDisposition.LATE,
                DeliveryReason.DEADLINE_EXPIRED,
                "ignored",
                "late",
            ),
        )

    def test_row_8b_closed_otherwise_is_closed_request(self):
        for extra in ({}, {"deadline": 31, **EXPIRED}, {"deadline": 30}):
            with self.subTest(extra=extra):
                got = classify_delivery(facts(**{**CLOSED, **extra}))
                self.assertEqual(
                    got,
                    decision(
                        "record",
                        DeliveryDisposition.IGNORED,
                        DeliveryReason.CLOSED_REQUEST,
                        "ignored",
                        "closed_request",
                    ),
                )

    def test_row_9_open_at_deadline_expires_then_records_late(self):
        got = classify_delivery(facts(deadline=30, **OPEN))
        self.assertEqual(
            got,
            decision(
                "expire_then_record",
                DeliveryDisposition.LATE,
                DeliveryReason.DEADLINE_EXPIRED,
                "ignored",
                "late",
            ),
        )

    def test_row_11_otherwise_applies(self):
        for deadline in (None, 31):
            with self.subTest(deadline=deadline):
                got = classify_delivery(facts(deadline=deadline, **OPEN))
                self.assertEqual(
                    got,
                    decision(
                        "apply",
                        DeliveryDisposition.APPLIED,
                        DeliveryReason.RESPONSE_APPLIED,
                        "applied",
                        None,
                    ),
                )

    def test_first_match_wins_over_later_rows(self):
        got = classify_delivery(
            facts(delivery_known=True, delivery_identical=True, message_conflicts=True, sent_at=1)
        )
        self.assertEqual(got.result_status, "ignored")
        self.assertEqual(got.action, "none")


if __name__ == "__main__":
    unittest.main()
