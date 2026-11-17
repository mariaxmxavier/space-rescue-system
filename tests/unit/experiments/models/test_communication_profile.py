"""Validation of the communication profile value."""

import unittest
from decimal import Decimal

from rescue.experiments.models.scenario.communication_profile import CommunicationProfile


class CommunicationProfileTests(unittest.TestCase):
    def test_negative_communication_delay_and_unbounded_profile_rule_are_rejected(self):
        with self.assertRaises(ValueError):
            CommunicationProfile("PROFILE-1", "SHIP-1", -1, 0, 0)
        with self.assertRaises(ValueError):
            CommunicationProfile(
                "PROFILE-1",
                "SHIP-1",
                0,
                0,
                0,
                loss_rule=(1, 1),
            )
        with self.assertRaisesRegex(ValueError, "cannot also be duplicated"):
            CommunicationProfile(
                "PROFILE-1", "SHIP-1", 0, 0, 0, loss_rule=(1,), duplication_rule=(1,)
            )
        with self.assertRaisesRegex(ValueError, "cannot also be duplicated"):
            CommunicationProfile(
                "PROFILE-1", "SHIP-1", 0, 0, 0, loss_rule=(1,), reordering_rule=(1,)
            )
        for rule in ((True,), (Decimal("1"),), (0,), (-1,)):
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                CommunicationProfile("PROFILE-1", "SHIP-1", 0, 0, 0, reordering_rule=rule)


if __name__ == "__main__":
    unittest.main()
