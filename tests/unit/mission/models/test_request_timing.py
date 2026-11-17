"""Request timing projection tests."""

import unittest
from decimal import Decimal

from rescue.mission.models.projections.request_timing import RequestTiming
from rescue.values import DomainValidationError


class RequestTimingTests(unittest.TestCase):
    def test_pending_request_has_no_receipt_and_no_elapsed_time(self):
        timing = RequestTiming(
            submitted_at=10,
            response_received_at=None,
            waiting_seconds=3,
            response_elapsed_seconds=None,
        )

        self.assertIsNone(timing.response_received_at)
        self.assertEqual(timing.waiting_seconds, Decimal("3"))
        self.assertIsNone(timing.response_elapsed_seconds)

    def test_answered_request_waits_zero_and_elapses_receipt_minus_submission(self):
        timing = RequestTiming(
            submitted_at=10,
            response_received_at=17,
            waiting_seconds=0,
            response_elapsed_seconds=7,
        )

        self.assertEqual(timing.waiting_seconds, Decimal("0"))
        self.assertEqual(timing.response_elapsed_seconds, Decimal("7"))

    def test_receipt_at_submission_time_is_allowed(self):
        timing = RequestTiming(
            submitted_at=10,
            response_received_at=10,
            waiting_seconds=0,
            response_elapsed_seconds=0,
        )

        self.assertEqual(timing.response_elapsed_seconds, Decimal("0"))

    def test_decimal_text_inputs_are_normalised(self):
        timing = RequestTiming(
            submitted_at="10.5",
            response_received_at="12.5",
            waiting_seconds="0",
            response_elapsed_seconds="2",
        )

        self.assertEqual(timing.submitted_at, Decimal("10.5"))
        self.assertEqual(timing.response_received_at, Decimal("12.5"))
        self.assertEqual(timing.response_elapsed_seconds, Decimal("2"))

    def test_receipt_before_submission_is_rejected(self):
        with self.assertRaisesRegex(
            DomainValidationError, "response receipt cannot precede submission"
        ):
            RequestTiming(
                submitted_at=10,
                response_received_at=9,
                waiting_seconds=0,
                response_elapsed_seconds=None,
            )

    def test_elapsed_time_without_receipt_is_rejected(self):
        with self.assertRaisesRegex(
            DomainValidationError, "response elapsed time requires a receipt time"
        ):
            RequestTiming(
                submitted_at=10,
                response_received_at=None,
                waiting_seconds=0,
                response_elapsed_seconds=5,
            )

    def test_answered_request_with_waiting_time_is_rejected(self):
        with self.assertRaisesRegex(
            DomainValidationError, "response timing projection is inconsistent"
        ):
            RequestTiming(
                submitted_at=10,
                response_received_at=17,
                waiting_seconds=2,
                response_elapsed_seconds=7,
            )

    def test_elapsed_time_not_equal_to_receipt_minus_submission_is_rejected(self):
        with self.assertRaisesRegex(
            DomainValidationError, "response timing projection is inconsistent"
        ):
            RequestTiming(
                submitted_at=10,
                response_received_at=17,
                waiting_seconds=0,
                response_elapsed_seconds=6,
            )

    def test_answered_request_without_elapsed_time_is_rejected(self):
        with self.assertRaisesRegex(
            DomainValidationError, "response timing projection is inconsistent"
        ):
            RequestTiming(
                submitted_at=10,
                response_received_at=17,
                waiting_seconds=0,
                response_elapsed_seconds=None,
            )

    def test_negative_submission_time_is_rejected(self):
        with self.assertRaisesRegex(
            DomainValidationError, "instant must be finite and nonnegative"
        ):
            RequestTiming(
                submitted_at=-1,
                response_received_at=None,
                waiting_seconds=0,
                response_elapsed_seconds=None,
            )


if __name__ == "__main__":
    unittest.main()
