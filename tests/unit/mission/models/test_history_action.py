"""History action vocabulary tests."""

import unittest

from rescue.mission.models.vocabulary.history_action import HistoryAction


class HistoryActionTest(unittest.TestCase):
    def test_values_are_exactly_the_closed_history_vocabulary(self):
        self.assertEqual(
            [member.value for member in HistoryAction],
            [
                "request_created",
                "accepted",
                "partially_accepted",
                "refused",
                "cancelled",
                "expired",
            ],
        )

    def test_members_are_strings_comparable_to_their_values(self):
        self.assertIsInstance(HistoryAction.REQUEST_CREATED, str)
        self.assertEqual(HistoryAction.PARTIALLY_ACCEPTED, "partially_accepted")
        self.assertIs(HistoryAction("refused"), HistoryAction.REFUSED)

    def test_pending_is_not_a_history_action(self):
        with self.assertRaises(ValueError):
            HistoryAction("pending")
