"""Request outcome vocabulary tests."""

import unittest

from rescue.mission.models.vocabulary.request_outcome import RequestOutcome


class RequestOutcomeTests(unittest.TestCase):
    def test_declares_six_members_in_order(self):
        self.assertEqual(
            [(member.name, member.value) for member in RequestOutcome],
            [
                ("PENDING", "pending"),
                ("ACCEPTED", "accepted"),
                ("PARTIALLY_ACCEPTED", "partially_accepted"),
                ("REFUSED", "refused"),
                ("CANCELLED", "cancelled"),
                ("EXPIRED", "expired"),
            ],
        )

    def test_value_lookup_returns_member(self):
        self.assertIs(RequestOutcome("accepted"), RequestOutcome.ACCEPTED)

    def test_unknown_value_is_rejected(self):
        with self.assertRaises(ValueError):
            RequestOutcome("acepted")

    def test_member_equals_its_string_value(self):
        self.assertEqual(RequestOutcome.ACCEPTED, "accepted")

    def test_final_returns_the_five_non_pending_members(self):
        self.assertEqual(
            RequestOutcome.final(),
            (
                RequestOutcome.ACCEPTED,
                RequestOutcome.PARTIALLY_ACCEPTED,
                RequestOutcome.REFUSED,
                RequestOutcome.CANCELLED,
                RequestOutcome.EXPIRED,
            ),
        )
