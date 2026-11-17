"""Mission registration input tests."""

import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal

from rescue.mission.models.mission.mission_data import MissionData
from rescue.values import DomainValidationError


def registration(**overrides):
    fields = {
        "mission_id": "mission-1",
        "station_name": "Station A",
        "people_count": 10,
        "created_at": "0",
    }
    return MissionData(**(fields | overrides))


class MissionDataTests(unittest.TestCase):
    def test_keeps_valid_registration_fields(self):
        mission = registration(
            mission_id="mission-1",
            station_name="Station A",
            people_count=10,
            created_at="5",
        )

        self.assertEqual(mission.mission_id, "mission-1")
        self.assertEqual(mission.station_name, "Station A")
        self.assertEqual(mission.people_count, 10)
        self.assertEqual(mission.created_at, Decimal("5"))

    def test_decimal_and_string_instants_normalise_to_the_same_instant(self):
        from_decimal = registration(created_at=Decimal("1.50")).created_at
        from_string = registration(created_at="1.50").created_at

        self.assertEqual(from_decimal, from_string)
        self.assertEqual(from_decimal, Decimal("1.50"))
        self.assertEqual(str(from_decimal), "1.50")

    def test_float_instant_is_rejected_rather_than_normalised(self):
        with self.assertRaises(DomainValidationError) as context:
            registration(created_at=1.50)

        self.assertEqual(str(context.exception), "instant must be an integer or decimal string")

    def test_blank_or_non_string_mission_id_is_rejected(self):
        for mission_id in ("", "   ", 7):
            with self.subTest(mission_id=mission_id):
                with self.assertRaises(DomainValidationError) as context:
                    registration(mission_id=mission_id)

                self.assertEqual(str(context.exception), "identifier must be a nonblank string")

    def test_blank_or_non_string_station_name_is_rejected(self):
        for station_name in ("", "  ", None):
            with self.subTest(station_name=station_name):
                with self.assertRaises(DomainValidationError) as context:
                    registration(station_name=station_name)

                self.assertEqual(str(context.exception), "station name must be a nonblank string")

    def test_non_positive_or_non_integer_people_count_is_rejected(self):
        for people_count in (0, -1, True, 2.0, "3"):
            with self.subTest(people_count=people_count):
                with self.assertRaises(DomainValidationError) as context:
                    registration(people_count=people_count)

                self.assertEqual(str(context.exception), "quantity must be a positive integer")

    def test_invalid_instant_is_rejected(self):
        cases = (
            (-1, "instant must be finite and nonnegative"),
            ("-1", "instant must be finite and nonnegative"),
            ("NaN", "instant must be finite and nonnegative"),
            (True, "instant must be an integer or decimal string"),
            ("abc", "instant must be a valid decimal value"),
        )
        for created_at, message in cases:
            with self.subTest(created_at=created_at):
                with self.assertRaises(DomainValidationError) as context:
                    registration(created_at=created_at)

                self.assertEqual(str(context.exception), message)

    def test_registration_is_immutable(self):
        mission = registration()

        with self.assertRaises(FrozenInstanceError):
            mission.people_count = 3
