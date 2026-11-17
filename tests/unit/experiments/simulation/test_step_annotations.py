"""Step signatures name the domain types they accept and return."""

import unittest
from typing import get_type_hints

from rescue.experiments.simulation.schedule_request_events import schedule_request_events
from rescue.experiments.simulation.schedule_response import schedule_response
from rescue.experiments.simulation.scripted_outcome import scripted_outcome
from rescue.mission.models import Mission, RequestOutcome, SeatRequest


class StepAnnotationTests(unittest.TestCase):
    def test_scripted_outcome_returns_a_request_outcome_and_seats(self):
        hints = get_type_hints(scripted_outcome)

        self.assertEqual(hints["return"], tuple[RequestOutcome, int])

    def test_schedule_request_events_types_its_request(self):
        self.assertIs(get_type_hints(schedule_request_events)["request"], SeatRequest)

    def test_schedule_response_types_its_mission_and_request(self):
        hints = get_type_hints(schedule_response)

        self.assertIs(hints["mission"], Mission)
        self.assertIs(hints["request"], SeatRequest)
