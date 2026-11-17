"""TimelineEvent priority defaults and kind validation."""

import unittest

from rescue.experiments.timeline.timeline_event import TimelineEvent
from rescue.values import DomainValidationError


class TimelineEventTests(unittest.TestCase):
    def test_expiration_priority_is_defaulted_to_zero_and_other_events_to_one(self):
        expiration = TimelineEvent(1, "expire", 1)
        response = TimelineEvent(1, "response", 1)

        self.assertEqual(expiration.priority, 0)
        self.assertEqual(response.priority, 1)

    def test_blank_kind_is_rejected(self):
        with self.assertRaises(DomainValidationError):
            TimelineEvent(1, "   ", 1)


if __name__ == "__main__":
    unittest.main()
