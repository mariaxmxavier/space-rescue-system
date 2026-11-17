"""Mission registration rule tests."""

import unittest

from rescue.mission.models.mission.mission import Mission
from rescue.mission.models.mission.mission_data import MissionData
from rescue.mission.rules.register import register
from rescue.values import DomainValidationError


def registration():
    return MissionData(
        mission_id="mission-1",
        station_name="Station A",
        people_count=10,
        created_at="0",
    )


def mission():
    return Mission(
        mission_id="mission-1",
        station_name="Station A",
        people_count=10,
        created_at="0",
    )


class RegisterTests(unittest.TestCase):
    def test_rejects_anything_other_than_mission_data(self):
        for value in (None, {"mission_id": "mission-1"}, mission()):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(DomainValidationError) as context:
                    register(value)

                self.assertEqual(
                    str(context.exception),
                    "mission registration requires MissionData",
                )

    def test_returns_mission_with_no_requests_and_no_history(self):
        created = register(registration())

        self.assertIsInstance(created, Mission)
        self.assertEqual(created.mission_id, "mission-1")
        self.assertEqual(created.station_name, "Station A")
        self.assertEqual(created.people_count, 10)
        self.assertEqual(created.created_at, mission().created_at)
        self.assertEqual(created.requests, ())
        self.assertEqual(created.history, ())
