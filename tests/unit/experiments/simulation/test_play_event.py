"""play_event dispatches a timeline event to the step that handles its kind."""

import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from rescue.experiments.simulation.play_event import play_event
from rescue.experiments.timeline import TimelineEvent
from rescue.values import DomainValidationError

MODULE = "rescue.experiments.simulation.play_event"


def event_of(kind: str, payload: object = "payload") -> TimelineEvent:
    return TimelineEvent(instant=Decimal("3"), kind=kind, scenario_sequence=1, payload=payload)


class PlayEventTests(unittest.TestCase):
    def test_mobilise_passes_payload_as_mission_id(self) -> None:
        session = MagicMock()
        with patch(f"{MODULE}.mobilise_mission") as step:
            play_event(session, event_of("mobilise", "m-1"))
        step.assert_called_once_with(session, "m-1", Decimal("3"))

    def test_each_handler_kind_calls_its_step(self) -> None:
        for kind in ("availability", "expire", "response"):
            name = {
                "availability": "publish_availability",
                "expire": "expire_request",
                "response": "record_response",
            }[kind]
            with self.subTest(kind=kind), patch(f"{MODULE}.{name}") as step:
                session = MagicMock()
                event = event_of(kind)
                play_event(session, event)
                step.assert_called_once_with(session, event, Decimal("3"))

    def test_unknown_kind_raises(self) -> None:
        with self.assertRaises(DomainValidationError) as caught:
            play_event(MagicMock(), event_of("bogus"))
        self.assertEqual(str(caught.exception), "unknown scenario event kind: 'bogus'")


if __name__ == "__main__":
    unittest.main()
