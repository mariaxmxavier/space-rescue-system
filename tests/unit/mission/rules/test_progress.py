"""Mission progress rule tests."""

import copy
import unittest

from rescue.mission.models.mission.mission import Mission
from rescue.mission.models.mission.seat_request import SeatRequest
from rescue.mission.models.vocabulary import ProgressStatus
from rescue.mission.rules.progress import progress
from rescue.values import DomainValidationError


def mission_with(*requests, demand=10):
    return Mission(
        mission_id="mission-1",
        station_name="Station A",
        people_count=demand,
        created_at=0,
        requests=requests,
    )


def pending_request(seats):
    return SeatRequest(
        request_id="request-1",
        command_id="command-1",
        mission_id="mission-1",
        ship_id="ship-1",
        requested_seats=seats,
        confirmed_seats=0,
        outcome="pending",
        submitted_at=1,
    )


def answered_request(seats, confirmed, outcome):
    return SeatRequest(
        request_id="request-1",
        command_id="command-1",
        mission_id="mission-1",
        ship_id="ship-1",
        requested_seats=seats,
        confirmed_seats=confirmed,
        outcome=outcome,
        submitted_at=1,
        response_received_at=2,
        closed_at=2,
    )


class ProgressTests(unittest.TestCase):
    def test_complete_when_every_demanded_seat_is_confirmed(self):
        result = progress(mission_with(answered_request(10, 10, "accepted")))
        self.assertIs(result.status, ProgressStatus.COMPLETE)
        self.assertEqual(
            (result.demand, result.confirmed, result.pending, result.unconfirmed),
            (10, 10, 0, 0),
        )
        self.assertEqual(result.additional_needed, 0)

    def test_awaiting_responses_when_pending_seats_cover_the_rest(self):
        result = progress(mission_with(pending_request(10)))
        self.assertIs(result.status, ProgressStatus.AWAITING_RESPONSES)
        self.assertEqual(
            (result.confirmed, result.pending, result.unconfirmed, result.additional_needed),
            (0, 10, 10, 0),
        )

    def test_needs_more_help_when_seats_are_neither_confirmed_nor_pending(self):
        result = progress(mission_with(answered_request(10, 4, "partially_accepted")))
        self.assertIs(result.status, ProgressStatus.NEEDS_MORE_HELP)
        self.assertEqual(
            (result.confirmed, result.pending, result.unconfirmed, result.additional_needed),
            (4, 0, 6, 6),
        )

    def test_reading_progress_never_changes_the_mission(self):
        mission = mission_with(pending_request(6))
        original = copy.deepcopy(mission)
        first = progress(mission)
        self.assertEqual(progress(mission), first)
        self.assertEqual(mission, original)

    def test_rejects_a_value_that_is_not_a_mission(self):
        with self.assertRaisesRegex(DomainValidationError, "progress requires a Mission"):
            progress(pending_request(6))
