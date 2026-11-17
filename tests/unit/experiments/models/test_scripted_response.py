"""Validation of the scripted response rule."""

import unittest

from rescue.experiments.models.scenario.scripted_response import ScriptedResponse


class ScriptedResponseTests(unittest.TestCase):
    def test_accepted_response_defaults_to_no_confirmed_seats(self):
        response = ScriptedResponse("SHIP-1", 1, "accepted")
        self.assertIsNone(response.confirmed_seats)

    def test_unsupported_outcome_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsupported outcome"):
            ScriptedResponse("SHIP-1", 1, "unknown")

    def test_ordinal_must_be_positive(self):
        with self.assertRaises(ValueError):
            ScriptedResponse("SHIP-1", 0, "refused")

    def test_refused_cannot_confirm_seats(self):
        with self.assertRaisesRegex(ValueError, "cannot confirm seats"):
            ScriptedResponse("SHIP-1", 1, "refused", 2)

    def test_partial_requires_confirmed_seats(self):
        with self.assertRaisesRegex(ValueError, "require confirmed seats"):
            ScriptedResponse("SHIP-1", 1, "partially_accepted", 0)


if __name__ == "__main__":
    unittest.main()
