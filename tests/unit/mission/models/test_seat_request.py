"""Seat request value tests."""

import dataclasses
import unittest
from decimal import Decimal

from rescue.mission.models.mission.seat_request import SeatRequest
from rescue.mission.models.vocabulary.request_outcome import RequestOutcome
from rescue.values import DomainValidationError


def pending_request(**overrides):
    fields = {
        "request_id": "request-1",
        "command_id": "command-1",
        "mission_id": "mission-1",
        "ship_id": "ship-1",
        "requested_seats": 4,
        "confirmed_seats": 0,
        "outcome": "pending",
        "submitted_at": 10,
        "response_deadline": 20,
    }
    return SeatRequest(**(fields | overrides))


class SeatRequestTests(unittest.TestCase):
    def test_new_pending_request_keeps_its_values_and_defaults(self):
        request = pending_request()
        self.assertIs(request.outcome, RequestOutcome.PENDING)
        self.assertEqual(request.requested_seats, 4)
        self.assertEqual(request.confirmed_seats, 0)
        self.assertEqual(request.submitted_at, Decimal("10"))
        self.assertEqual(request.response_deadline, Decimal("20"))
        self.assertIsNone(request.response_received_at)
        self.assertIsNone(request.closed_at)
        self.assertIsNone(request.quote_id)
        self.assertIsNone(request.revision_id)
        self.assertIsNone(request.decision_id)

    def test_outcome_accepts_member_or_string_value(self):
        self.assertIs(
            pending_request(outcome=RequestOutcome.ACCEPTED, confirmed_seats=4).outcome,
            RequestOutcome.ACCEPTED,
        )
        self.assertIs(
            pending_request(outcome="accepted", confirmed_seats=4).outcome,
            RequestOutcome.ACCEPTED,
        )

    def test_unknown_outcome_is_rejected_with_its_value(self):
        with self.assertRaisesRegex(DomainValidationError, "unknown request outcome: 'acepted'"):
            pending_request(outcome="acepted")

    def test_blank_identifiers_are_rejected(self):
        for field_name in ("request_id", "command_id", "mission_id", "ship_id"):
            with self.subTest(field=field_name):
                with self.assertRaisesRegex(
                    DomainValidationError, "identifier must be a nonblank string"
                ):
                    pending_request(**{field_name: "  "})

    def test_blank_optional_identifiers_are_rejected_with_their_label(self):
        for field_name, label in (
            ("quote_id", "quote id"),
            ("revision_id", "revision id"),
            ("decision_id", "decision id"),
        ):
            with self.subTest(field=field_name):
                with self.assertRaisesRegex(
                    DomainValidationError, f"{label} must be a nonblank identifier"
                ):
                    pending_request(**{field_name: " "})

    def test_optional_identifiers_are_kept_when_given(self):
        request = pending_request(
            quote_id="quote-1", revision_id="revision-1", decision_id="decision-1"
        )
        self.assertEqual(
            (request.quote_id, request.revision_id, request.decision_id),
            ("quote-1", "revision-1", "decision-1"),
        )

    def test_requested_seats_must_be_positive_integer(self):
        for seats in (0, -1, True):
            with self.subTest(seats=seats):
                with self.assertRaisesRegex(
                    DomainValidationError, "quantity must be a positive integer"
                ):
                    pending_request(requested_seats=seats)

    def test_confirmed_seats_must_be_nonnegative(self):
        with self.assertRaisesRegex(
            DomainValidationError, "quantity must be a nonnegative integer"
        ):
            pending_request(confirmed_seats=-1)

    def test_negative_instant_is_rejected(self):
        with self.assertRaisesRegex(
            DomainValidationError, "instant must be finite and nonnegative"
        ):
            pending_request(submitted_at=-1)

    def test_response_cannot_precede_submission(self):
        with self.assertRaisesRegex(
            DomainValidationError, "response_received_at cannot precede submission"
        ):
            pending_request(response_received_at=9)

    def test_closed_at_cannot_precede_submission(self):
        with self.assertRaisesRegex(DomainValidationError, "closed_at cannot precede submission"):
            pending_request(closed_at=9)

    def test_deadline_must_follow_submission(self):
        for deadline in (9, 10):
            with self.subTest(deadline=deadline):
                with self.assertRaisesRegex(
                    DomainValidationError, "response deadline must follow request submission"
                ):
                    pending_request(response_deadline=deadline)

    def test_response_must_precede_deadline(self):
        with self.assertRaisesRegex(
            DomainValidationError, "response received at or after deadline must expire"
        ):
            pending_request(outcome="accepted", confirmed_seats=4, response_received_at=20)

    def test_pending_request_cannot_confirm_seats(self):
        with self.assertRaisesRegex(DomainValidationError, "pending request cannot confirm seats"):
            pending_request(confirmed_seats=1)

    def test_accepted_request_must_confirm_all_requested_seats(self):
        with self.assertRaisesRegex(
            DomainValidationError, "accepted request must confirm all requested seats"
        ):
            pending_request(outcome="accepted", confirmed_seats=3)

    def test_accepted_request_with_full_confirmation_is_valid(self):
        request = pending_request(
            outcome="accepted", confirmed_seats=4, response_received_at=15, closed_at=15
        )
        self.assertEqual(request.confirmed_seats, 4)
        self.assertEqual(request.response_received_at, Decimal("15"))

    def test_partial_acceptance_must_confirm_a_positive_proper_subset(self):
        for confirmed in (0, 4):
            with self.subTest(confirmed=confirmed):
                with self.assertRaisesRegex(
                    DomainValidationError, "partial acceptance must confirm a positive subset"
                ):
                    pending_request(outcome="partially_accepted", confirmed_seats=confirmed)
        self.assertEqual(
            pending_request(outcome="partially_accepted", confirmed_seats=1).confirmed_seats, 1
        )

    def test_refused_cancelled_and_expired_requests_confirm_no_seats(self):
        for outcome in ("refused", "cancelled", "expired"):
            with self.subTest(outcome=outcome):
                with self.assertRaisesRegex(
                    DomainValidationError, f"{outcome} request cannot confirm seats"
                ):
                    pending_request(outcome=outcome, confirmed_seats=1)

    def test_cancelled_and_expired_requests_cannot_carry_a_response_time(self):
        for outcome in ("cancelled", "expired"):
            with self.subTest(outcome=outcome):
                with self.assertRaisesRegex(
                    DomainValidationError,
                    f"{outcome} request cannot invent a response receipt time",
                ):
                    pending_request(outcome=outcome, response_received_at=15)

    def test_refused_request_may_carry_a_response_time(self):
        refused = pending_request(outcome="refused", response_received_at=15, closed_at=15)
        self.assertEqual(refused.outcome, RequestOutcome.REFUSED)
        self.assertEqual(refused.closed_at, Decimal("15"))

    def test_request_is_immutable(self):
        request = pending_request()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            request.confirmed_seats = 1


if __name__ == "__main__":
    unittest.main()
