"""Delivery reason vocabulary tests."""

import unittest

from rescue.communication.models.vocabulary.delivery_reason import DeliveryReason

EXPECTED_VALUES = [
    "response_applied",
    "identity_conflict",
    "transport_loss",
    "unknown_request",
    "invalid_input",
    "closed_request",
    "deadline_expired",
    "unknown_mission",
    "unknown_ship",
    "insufficient_demand",
    "insufficient_capacity",
    "unavailable",
    "expired_quote",
    "revision_conflict",
    "duplicate_sequence",
]


class DeliveryReasonTest(unittest.TestCase):
    def test_values_are_exactly_the_closed_delivery_reason_vocabulary(self):
        self.assertEqual([member.value for member in DeliveryReason], EXPECTED_VALUES)

    def test_member_names_are_the_upper_case_of_their_values(self):
        self.assertEqual(
            [member.name for member in DeliveryReason],
            [value.upper() for value in EXPECTED_VALUES],
        )

    def test_value_lookup_returns_the_matching_member(self):
        self.assertIs(DeliveryReason("transport_loss"), DeliveryReason.TRANSPORT_LOSS)

    def test_unknown_value_is_rejected(self):
        with self.assertRaises(ValueError):
            DeliveryReason("unknown_reason")
