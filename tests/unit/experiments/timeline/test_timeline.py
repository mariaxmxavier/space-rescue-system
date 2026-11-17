"""Finite event ordering and horizon behavior for experiment timelines."""

import unittest
from decimal import Decimal

from rescue.experiments.timeline import Timeline, TimelineEvent


class TimelineTests(unittest.TestCase):
    def test_equal_time_events_order_by_priority_then_scenario_then_insertion(self):
        timeline = Timeline(horizon=10, event_budget=8)
        events = (
            TimelineEvent(5, "response", 1, payload="response-first"),
            TimelineEvent(5, "availability", 1, payload="availability-first"),
            TimelineEvent(5, "expire", 2, payload="expiration-later-sequence"),
            TimelineEvent(5, "response", 0, payload="response-early-sequence"),
            TimelineEvent(4, "response", 9, payload="earlier-time"),
        )
        for event in events:
            timeline.schedule(event)

        ordered = tuple(timeline.pop_next() for _ in events)

        self.assertEqual(
            tuple(event.payload for event in ordered),
            (
                "earlier-time",
                "expiration-later-sequence",
                "response-early-sequence",
                "response-first",
                "availability-first",
            ),
        )
        self.assertEqual(
            tuple(event.priority for event in ordered),
            (1, 0, 1, 1, 1),
        )

    def test_explicit_priority_and_insertion_order_break_remaining_ties(self):
        timeline = Timeline(horizon=Decimal("3"), event_budget=4)
        timeline.schedule(TimelineEvent(2, "response", 1, payload="inserted-first", priority=2))
        timeline.schedule(TimelineEvent(2, "response", 1, payload="explicit-first", priority=0))
        timeline.schedule(TimelineEvent(2, "response", 1, payload="inserted-third", priority=2))

        self.assertEqual(timeline.pop_next().payload, "explicit-first")
        self.assertEqual(timeline.pop_next().payload, "inserted-first")
        self.assertEqual(timeline.pop_next().payload, "inserted-third")

    def test_events_at_horizon_are_included_and_events_after_are_not_popped(self):
        timeline = Timeline(horizon=10, event_budget=4)
        timeline.schedule(TimelineEvent(10, "response", 1, payload="at-horizon"))
        timeline.schedule(TimelineEvent(Decimal("10.1"), "response", 2, payload="after-horizon"))

        self.assertEqual(timeline.pop_next().payload, "at-horizon")
        self.assertIsNone(timeline.pop_next())

    def test_scheduling_more_than_event_budget_is_rejected(self):
        timeline = Timeline(horizon=10, event_budget=1)
        timeline.schedule(TimelineEvent(1, "response", 1, payload="first"))

        with self.assertRaises(ValueError):
            timeline.schedule(TimelineEvent(2, "response", 2, payload="over-budget"))

        self.assertEqual(timeline.pop_next().payload, "first")
        self.assertIsNone(timeline.pop_next())

    def test_expiration_priority_is_defaulted_to_zero_and_other_events_to_one(self):
        expiration = TimelineEvent(1, "expire", 1)
        response = TimelineEvent(1, "response", 1)

        self.assertEqual(expiration.priority, 0)
        self.assertEqual(response.priority, 1)


if __name__ == "__main__":
    unittest.main()
