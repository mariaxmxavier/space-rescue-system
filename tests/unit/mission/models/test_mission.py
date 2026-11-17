"""Mission aggregate tests: identity rules, owned tuples and element types."""

import dataclasses
import unittest
from decimal import Decimal

from rescue.mission.models.mission.seat_request import SeatRequest

from rescue.mission.models.mission.mission import Mission
from rescue.mission.models.mission.request_history_entry import RequestHistoryEntry
from rescue.mission.models.vocabulary import HistoryAction, RequestOutcome
from rescue.values import DomainValidationError


def mission(**overrides):
    fields = {
        "mission_id": "mission-1",
        "station_name": "Station A",
        "people_count": 10,
        "created_at": "0",
    }
    return Mission(**(fields | overrides))


def seat_request():
    return SeatRequest(
        request_id="request-1",
        command_id="command-1",
        mission_id="mission-1",
        ship_id="ship-1",
        requested_seats=6,
        confirmed_seats=0,
        outcome=RequestOutcome.PENDING,
        submitted_at="1",
    )


def history_entry():
    return RequestHistoryEntry(
        event_id="event-1",
        mission_sequence=1,
        recorded_at="1",
        action=HistoryAction.REQUEST_CREATED,
        confirmed_seats_delta=0,
        pending_seats_delta=6,
        reason="requested",
    )


class MissionTests(unittest.TestCase):
    def test_new_mission_owns_no_requests_or_history(self):
        created = mission()

        self.assertEqual(created.requests, ())
        self.assertEqual(created.history, ())

    def test_blank_mission_id_is_rejected(self):
        with self.assertRaisesRegex(DomainValidationError, "identifier must be a nonblank string"):
            mission(mission_id=" ")

    def test_blank_station_name_is_rejected(self):
        with self.assertRaisesRegex(
            DomainValidationError, "station name must be a nonblank string"
        ):
            mission(station_name="  ")

    def test_non_positive_people_count_is_rejected(self):
        with self.assertRaisesRegex(DomainValidationError, "quantity must be a positive integer"):
            mission(people_count=0)

    def test_created_at_is_normalised_to_a_decimal_instant(self):
        self.assertEqual(mission(created_at="1.50").created_at, Decimal("1.50"))
        self.assertEqual(mission(created_at=3).created_at, Decimal("3"))

    def test_negative_created_at_is_rejected(self):
        with self.assertRaisesRegex(
            DomainValidationError, "instant must be finite and nonnegative"
        ):
            mission(created_at=-1)

    def test_requests_and_history_are_stored_as_tuples(self):
        request = seat_request()
        entry = history_entry()

        created = mission(requests=[request], history=[entry])

        self.assertEqual(created.requests, (request,))
        self.assertEqual(created.history, (entry,))
        self.assertIsInstance(created.requests, tuple)
        self.assertIsInstance(created.history, tuple)

    def test_string_requests_are_rejected_as_not_a_collection(self):
        with self.assertRaisesRegex(DomainValidationError, "not a collection of snapshot values"):
            mission(requests="request-1")

    def test_non_iterable_history_is_rejected(self):
        with self.assertRaises(TypeError):
            mission(history=5)

    def test_request_of_wrong_type_is_rejected(self):
        with self.assertRaisesRegex(
            DomainValidationError, "mission requests must be SeatRequest values"
        ):
            mission(requests=(history_entry(),))

    def test_history_entry_of_wrong_type_is_rejected(self):
        with self.assertRaisesRegex(
            DomainValidationError, "mission history must contain RequestHistoryEntry values"
        ):
            mission(history=(seat_request(),))

    def test_requests_and_history_are_kept_as_given_elements(self):
        request = seat_request()
        entry = history_entry()

        created = mission(requests=(request,), history=(entry,))

        self.assertIs(created.requests[0], request)
        self.assertIs(created.history[0], entry)

    def test_mission_is_immutable(self):
        created = mission()

        with self.assertRaises(dataclasses.FrozenInstanceError):
            created.station_name = "Station B"
