"""Recovery rejection vocabulary tests."""

import unittest

from rescue.communication.models.vocabulary.recovery_rejection import RecoveryRejection


class RecoveryRejectionTests(unittest.TestCase):
    def test_values_are_exactly_the_five_rejection_reasons(self):
        self.assertEqual(
            {member.value for member in RecoveryRejection},
            {
                "stale_session",
                "recovery_out_of_range",
                "recovery_limit",
                "recovery_in_progress",
                "sequence_rewind",
            },
        )

    def test_value_lookup_returns_member(self):
        self.assertIs(RecoveryRejection("recovery_limit"), RecoveryRejection.RECOVERY_LIMIT)

    def test_unknown_value_is_rejected(self):
        with self.assertRaises(ValueError):
            RecoveryRejection("recovery_limt")
