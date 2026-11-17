"""Request timing rule tests."""

import unittest
from decimal import Decimal

from rescue.mission.models.mission.seat_request import SeatRequest
from rescue.mission.rules.timing import timing
from rescue.values import DomainValidationError


def pending_request():
    return SeatRequest(
        request_id="request-1",
        command_id="command-1",
        mission_id="mission-1",
        ship_id="ship-1",
        requested_seats=4,
        confirmed_seats=0,
        outcome="pending",
        submitted_at=10,
    )


def answered_request():
    return SeatRequest(
        request_id="request-1",
        command_id="command-1",
        mission_id="mission-1",
        ship_id="ship-1",
        requested_seats=4,
        confirmed_seats=4,
        outcome="accepted",
        submitted_at=10,
        response_received_at=17,
        closed_at=17,
    )


class TimingRuleTests(unittest.TestCase):
    def test_non_seat_request_is_rejected(self):
        with self.assertRaisesRegex(DomainValidationError, "timing requires a SeatRequest"):
            timing("request-1", 12)

    def test_observation_before_submission_is_rejected(self):
        with self.assertRaisesRegex(
            DomainValidationError, "observation time cannot precede request submission"
        ):
            timing(pending_request(), 9)

    def test_pending_request_waits_until_observation_with_no_elapsed_time(self):
        result = timing(pending_request(), 15)

        self.assertEqual(result.submitted_at, Decimal("10"))
        self.assertIsNone(result.response_received_at)
        self.assertEqual(result.waiting_seconds, Decimal("5"))
        self.assertIsNone(result.response_elapsed_seconds)

    def test_pending_request_observed_at_submission_has_waited_zero(self):
        result = timing(pending_request(), 10)

        self.assertEqual(result.waiting_seconds, Decimal("0"))

    def test_answered_request_waits_zero_and_elapses_receipt_minus_submission(self):
        result = timing(answered_request(), 40)

        self.assertEqual(result.response_received_at, Decimal("17"))
        self.assertEqual(result.waiting_seconds, Decimal("0"))
        self.assertEqual(result.response_elapsed_seconds, Decimal("7"))
