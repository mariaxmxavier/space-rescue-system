"""Add seat request rule tests."""

import copy
import unittest

from rescue.mission.models.mission.mission import Mission
from rescue.mission.models.mission.seat_request import SeatRequest
from rescue.mission.models.vocabulary.history_action import HistoryAction
from rescue.mission.rules.add_request import add_request
from rescue.mission.rules.progress import progress
from rescue.values import DomainValidationError, TransitionContext


def new_mission(demand=10, created_at="0"):
    return Mission(
        mission_id="mission-1",
        station_name="Station A",
        people_count=demand,
        created_at=created_at,
    )


def pending_request(request_id="request-1", seats=6, submitted_at="1", **overrides):
    fields = {
        "request_id": request_id,
        "command_id": f"command-{request_id}",
        "mission_id": "mission-1",
        "ship_id": "ship-1",
        "requested_seats": seats,
        "confirmed_seats": 0,
        "outcome": "pending",
        "submitted_at": submitted_at,
        "revision_id": "revision-1",
    }
    return SeatRequest(**(fields | overrides))


def context(event_id="created", at="1"):
    return TransitionContext(event_id=event_id, at=at, reason="test")


class AddRequestTests(unittest.TestCase):
    def assertRejected(self, message, mission, request, transition):
        with self.assertRaises(DomainValidationError) as raised:
            add_request(mission, request, transition)
        self.assertEqual(str(raised.exception), message)

    def test_appends_pending_request_and_a_creation_row_without_changing_the_input(self):
        original = new_mission()

        mission = add_request(original, pending_request(), context())

        self.assertEqual(original.requests, ())
        self.assertEqual(original.history, ())
        self.assertEqual([request.request_id for request in mission.requests], ["request-1"])
        self.assertEqual(len(mission.history), 1)
        entry = mission.history[0]
        self.assertIs(entry.action, HistoryAction.REQUEST_CREATED)
        self.assertEqual(entry.mission_sequence, 1)
        self.assertEqual(entry.pending_seats_delta, 6)
        self.assertEqual(entry.confirmed_seats_delta, 0)

    def test_request_that_fills_the_remaining_demand_is_accepted(self):
        mission = add_request(new_mission(), pending_request(seats=6), context("first", "1"))

        mission = add_request(
            mission,
            pending_request("request-2", seats=4, submitted_at="2"),
            context("second", "2"),
        )

        self.assertEqual(len(mission.requests), 2)
        self.assertEqual(mission.history[1].mission_sequence, 2)

    def test_rejects_arguments_of_the_wrong_type(self):
        self.assertRejected(
            "add_request requires Mission and SeatRequest values",
            "mission",
            pending_request(),
            context(),
        )
        self.assertRejected(
            "add_request requires Mission and SeatRequest values",
            new_mission(),
            "request",
            context(),
        )
        self.assertRejected(
            "add_request requires a TransitionContext",
            new_mission(),
            pending_request(),
            "context",
        )

    def test_rejects_request_for_another_mission(self):
        self.assertRejected(
            "request mission_id does not match its owner",
            new_mission(),
            pending_request(mission_id="mission-2"),
            context(),
        )

    def test_rejects_request_that_is_not_pending_with_zero_confirmed(self):
        self.assertRejected(
            "new seat requests must be pending with zero confirmed",
            new_mission(),
            pending_request(outcome="refused"),
            context(),
        )
        self.assertRejected(
            "new seat requests must be pending with zero confirmed",
            new_mission(),
            pending_request(outcome="accepted", confirmed_seats=6),
            context(),
        )

    def test_rejects_submission_time_that_differs_from_transition_time(self):
        self.assertRejected(
            "request submission time must match transition time",
            new_mission(),
            pending_request(submitted_at="2"),
            context(at="1"),
        )

    def test_rejects_request_submitted_before_mission_registration(self):
        self.assertRejected(
            "request cannot precede mission registration",
            new_mission(created_at="5"),
            pending_request(submitted_at="3"),
            context(at="3"),
        )

    def test_rejects_repeated_request_identity_within_the_mission(self):
        mission = add_request(new_mission(), pending_request(seats=6), context("first", "1"))

        self.assertRejected(
            "request identity must be unique within its mission",
            mission,
            pending_request(seats=1, submitted_at="2"),
            context("second", "2"),
        )

    def test_rejects_request_above_the_remaining_demand(self):
        mission = add_request(new_mission(), pending_request(seats=6), context("first", "1"))

        self.assertRejected(
            "request exceeds remaining mission demand",
            mission,
            pending_request("request-2", seats=5, submitted_at="2"),
            context("second", "2"),
        )

    def test_rejects_repeated_event_identity_in_history(self):
        mission = add_request(new_mission(), pending_request(seats=6), context("created", "1"))

        self.assertRejected(
            "history event identity must be unique per mission",
            mission,
            pending_request("request-2", seats=2, submitted_at="2"),
            context("created", "2"),
        )

    def test_over_demand_request_leaves_mission_unchanged(self):
        mission = add_request(new_mission(), pending_request(seats=6), context("created", "1"))
        original = copy.deepcopy(mission)

        with self.assertRaises(ValueError):
            add_request(
                mission,
                pending_request("request-2", seats=5, submitted_at="2"),
                context("over-demand", "2"),
            )
        self.assertEqual(mission, original)
        self.assertEqual(progress(mission).additional_needed, 4)


if __name__ == "__main__":
    unittest.main()
