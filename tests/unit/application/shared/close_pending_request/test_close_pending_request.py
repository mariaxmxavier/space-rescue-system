"""close_pending_request tests."""

import unittest
from dataclasses import replace

from rescue.application.shared.close_pending_request import close_pending_request
from rescue.application.shared.make_result import make_result
from rescue.mission import rules as mission_rules
from rescue.mission.models import Mission, RequestOutcome, SeatRequest
from rescue.values import TransitionContext
from tests.unit.application.services.fakes import FakeIds, empty_state

SUBMITTED = 100
DEADLINE = 200
LATER = 150


def state_with_pending_request():
    mission = Mission("MISSION-1", "Station One", 6, 0)
    request = SeatRequest(
        request_id="REQUEST-1",
        command_id="COMMAND-1",
        mission_id="MISSION-1",
        ship_id="SHIP-1",
        requested_seats=2,
        confirmed_seats=0,
        outcome=RequestOutcome.PENDING,
        submitted_at=SUBMITTED,
        response_deadline=DEADLINE,
    )
    mission = mission_rules.add_request(
        mission, request, TransitionContext("EVENT-0", SUBMITTED, "request_created")
    )
    return replace(empty_state(), missions=(mission,))


def reject_always(request, instant):
    return make_result("rejected", reason="invalid_input")


class ClosePendingRequestTests(unittest.TestCase):
    """close_pending_request closes one pending request by id, or refuses without changing state.

    What: returns the new state and a Result for the closure.
    When called: by tests of the shared closer used by cancel_request and expire_request.
    Why: both closures must share one order of checks and leave the state alone on any refusal.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def setUp(self):
        self.state = state_with_pending_request()
        self.ids = FakeIds()

    def close(self, state, mission_id="MISSION-1", request_id="REQUEST-1", at=LATER, **kwargs):
        return close_pending_request(
            state,
            mission_id,
            request_id,
            RequestOutcome.CANCELLED,
            at,
            "request_cancelled",
            id_source=self.ids,
            **{"event_first": False, **kwargs},
        )

    def test_unknown_mission_is_rejected(self):
        state, result = self.close(self.state, mission_id="MISSION-9")
        self.assertEqual((result.status, result.reason), ("rejected", "unknown_mission"))
        self.assertIs(state, self.state)

    def test_unknown_request_is_rejected(self):
        state, result = self.close(self.state, request_id="REQUEST-9")
        self.assertEqual((result.status, result.reason), ("rejected", "unknown_request"))
        self.assertIs(state, self.state)

    def test_closed_request_is_ignored(self):
        closed, first = self.close(self.state)
        state, result = self.close(closed)
        self.assertEqual((first.status, result.status), ("applied", "ignored"))
        self.assertEqual(result.reason, "closed_request")
        self.assertIs(state, closed)

    def test_guard_rejection_returns_the_state_unchanged(self):
        state, result = self.close(self.state, guard=reject_always)
        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))
        self.assertIs(state, self.state)
        self.assertEqual(self.ids.counts["event"], 0)

    def test_success_closes_the_request_with_the_outcome(self):
        state, result = self.close(self.state)
        self.assertEqual(result.status, "applied")
        self.assertEqual(result.value.outcome, RequestOutcome.CANCELLED)
        self.assertEqual(state.missions[0].requests[0], result.value)

    def test_domain_error_is_mapped_to_a_reason(self):
        state, result = close_pending_request(
            self.state,
            "MISSION-1",
            "REQUEST-1",
            RequestOutcome.CANCELLED,
            50,
            "request_cancelled",
            id_source=self.ids,
            event_first=False,
        )
        self.assertEqual(result.status, "rejected")
        self.assertIs(state, self.state)

    def test_event_first_draws_the_event_id_before_an_invalid_instant_is_rejected(self):
        state, result = self.close(self.state, event_first=True, at="invalid")
        self.assertEqual(result.status, "rejected")
        self.assertIs(state, self.state)
        self.assertEqual(self.ids.counts["event"], 1)

    def test_instant_first_draws_no_event_id_for_an_invalid_instant(self):
        state, result = self.close(self.state, event_first=False, at="invalid")
        self.assertEqual(result.status, "rejected")
        self.assertIs(state, self.state)
        self.assertEqual(self.ids.counts["event"], 0)
