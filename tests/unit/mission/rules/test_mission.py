"""Pure mission accounting and transition tests."""

import copy
import unittest

from rescue.mission.models import MissionData, SeatRequest
from rescue.mission.rules import add_request, apply_outcome, progress, register
from rescue.values import TransitionContext


def new_mission(demand=10):
    return register(
        MissionData(
            mission_id="mission-1",
            station_name="Station A",
            people_count=demand,
            created_at="0",
        )
    )


def new_request(request_id="request-1", seats=6):
    return SeatRequest(
        request_id=request_id,
        command_id=f"command-{request_id}",
        mission_id="mission-1",
        ship_id="ship-1",
        requested_seats=seats,
        confirmed_seats=0,
        outcome="pending",
        submitted_at="1",
        revision_id="revision-1",
    )


def context(event_id, at):
    return TransitionContext(event_id=event_id, at=at, reason="test")


class MissionRuleTests(unittest.TestCase):
    def test_pending_and_all_terminal_outcomes_have_correct_accounting(self):
        cases = (
            ("accepted", 6, 6),
            ("partially_accepted", 4, 4),
            ("refused", 0, 0),
            ("cancelled", 0, 0),
            ("expired", 0, 0),
        )

        for outcome, confirmed, expected_confirmed in cases:
            with self.subTest(outcome=outcome):
                mission = add_request(new_mission(), new_request(), context("created", "1"))
                pending = progress(mission)
                self.assertEqual(pending.demand, 10)
                self.assertEqual(pending.confirmed, 0)
                self.assertEqual(pending.pending, 6)
                self.assertEqual(mission.requests[0].outcome, "pending")

                changed = apply_outcome(
                    mission,
                    "request-1",
                    outcome,
                    confirmed,
                    context("outcome", "2"),
                )
                result = progress(changed)
                self.assertEqual(result.demand, 10)
                self.assertEqual(result.confirmed, expected_confirmed)
                self.assertEqual(result.pending, 0)
                request = changed.requests[0]
                self.assertEqual(request.outcome, outcome)
                self.assertEqual(request.confirmed_seats, expected_confirmed)
                self.assertEqual(request.closed_at, 2)
                self.assertEqual(
                    [entry.event_id for entry in changed.history],
                    ["created", "outcome"],
                )

    def test_partial_acceptance_is_terminal_and_releases_unconfirmed_seats(self):
        mission = add_request(new_mission(), new_request(), context("created", "1"))
        accepted = apply_outcome(
            mission,
            "request-1",
            "partially_accepted",
            4,
            context("partial", "2"),
        )

        result = progress(accepted)
        self.assertEqual(
            (result.confirmed, result.pending, result.unconfirmed, result.additional_needed),
            (4, 0, 6, 6),
        )
        self.assertEqual(result.status, "needs_more_help")

        with self.assertRaises(ValueError):
            apply_outcome(
                accepted,
                "request-1",
                "accepted",
                6,
                context("late-outcome", "3"),
            )
        self.assertEqual(len(accepted.history), 2)

    def test_full_acceptance_completes_mission_but_pending_demand_does_not(self):
        mission = add_request(new_mission(), new_request(seats=10), context("created", "1"))
        pending = progress(mission)
        self.assertEqual(pending.confirmed, 0)
        self.assertEqual(pending.pending, 10)
        self.assertEqual(pending.status, "awaiting_responses")

        complete = apply_outcome(
            mission,
            "request-1",
            "accepted",
            10,
            context("accepted", "2"),
        )
        result = progress(complete)
        self.assertEqual(result.demand, 10)
        self.assertEqual(result.confirmed, 10)
        self.assertEqual(result.pending, 0)
        self.assertEqual(result.additional_needed, 0)
        self.assertEqual(result.status, "complete")

    def test_invalid_confirmation_and_excess_request_leave_mission_unchanged(self):
        mission = add_request(new_mission(), new_request(), context("created", "1"))
        original = copy.deepcopy(mission)

        for invalid in (-1, 7, 1.5, True):
            with self.subTest(confirmed=invalid):
                with self.assertRaises(ValueError):
                    apply_outcome(
                        mission,
                        "request-1",
                        "partially_accepted",
                        invalid,
                        context(f"invalid-{invalid}", "2"),
                    )
                self.assertEqual(progress(mission).pending, 6)
                self.assertEqual(len(mission.history), 1)
                self.assertEqual(mission, original)

        with self.assertRaises(ValueError):
            add_request(
                mission,
                new_request(request_id="request-2", seats=5),
                context("over-demand", "2"),
            )
        self.assertEqual(mission, original)
        self.assertEqual(progress(mission).additional_needed, 4)

    def test_request_deadline_must_follow_submission_and_receipt(self):
        with self.assertRaises(ValueError):
            SeatRequest(
                request_id="deadline-before",
                command_id="command-deadline-before",
                mission_id="mission-1",
                ship_id="ship-1",
                requested_seats=1,
                confirmed_seats=0,
                outcome="pending",
                submitted_at=2,
                response_deadline=1,
            )
        with self.assertRaises(ValueError):
            SeatRequest(
                request_id="deadline-equal",
                command_id="command-deadline-equal",
                mission_id="mission-1",
                ship_id="ship-1",
                requested_seats=1,
                confirmed_seats=0,
                outcome="pending",
                submitted_at=2,
                response_deadline=2,
            )

        with self.assertRaises(ValueError):
            SeatRequest(
                request_id="response-at-deadline",
                command_id="command-response-at-deadline",
                mission_id="mission-1",
                ship_id="ship-1",
                requested_seats=1,
                confirmed_seats=1,
                outcome="accepted",
                submitted_at=2,
                response_received_at=5,
                response_deadline=5,
                closed_at=5,
            )


if __name__ == "__main__":
    unittest.main()
