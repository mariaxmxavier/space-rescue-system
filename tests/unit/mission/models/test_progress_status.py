"""Closed progress status vocabulary tests."""

import unittest

from rescue.mission.models.vocabulary.progress_status import ProgressStatus


class ProgressStatusTests(unittest.TestCase):
    def test_has_exactly_the_three_progress_values(self):
        self.assertEqual(
            {status.value for status in ProgressStatus},
            {"complete", "awaiting_responses", "needs_more_help"},
        )

    def test_value_lookup_returns_the_member(self):
        self.assertIs(ProgressStatus("complete"), ProgressStatus.COMPLETE)
        self.assertIs(ProgressStatus("awaiting_responses"), ProgressStatus.AWAITING_RESPONSES)
        self.assertIs(ProgressStatus("needs_more_help"), ProgressStatus.NEEDS_MORE_HELP)

    def test_members_equal_their_wire_strings(self):
        self.assertEqual(ProgressStatus.COMPLETE, "complete")
        self.assertEqual(ProgressStatus.AWAITING_RESPONSES, "awaiting_responses")
        self.assertEqual(ProgressStatus.NEEDS_MORE_HELP, "needs_more_help")

    def test_unknown_value_is_rejected(self):
        with self.assertRaises(ValueError):
            ProgressStatus("finished")


if __name__ == "__main__":
    unittest.main()
