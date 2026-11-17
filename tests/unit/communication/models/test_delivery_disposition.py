"""Closed delivery disposition vocabulary tests."""

import unittest

from rescue.communication.models.vocabulary.delivery_disposition import DeliveryDisposition


class DeliveryDispositionTests(unittest.TestCase):
    def test_has_exactly_the_five_disposition_values(self):
        self.assertEqual(
            {disposition.value for disposition in DeliveryDisposition},
            {"applied", "ignored", "lost", "rejected", "late"},
        )

    def test_value_lookup_returns_the_member(self):
        self.assertIs(DeliveryDisposition("lost"), DeliveryDisposition.LOST)

    def test_members_equal_their_wire_strings(self):
        self.assertEqual(DeliveryDisposition.LOST, "lost")

    def test_unknown_value_is_rejected(self):
        with self.assertRaises(ValueError):
            DeliveryDisposition("duplicated")


if __name__ == "__main__":
    unittest.main()
