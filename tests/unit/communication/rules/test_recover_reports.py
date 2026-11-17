"""Recovery rule tests."""

import unittest

from rescue.communication.models.recovery.decision_report import DecisionReport
from rescue.communication.models.recovery.recovery_request import RecoveryRequest
from rescue.communication.models.recovery.sequence_control import SequenceControl
from rescue.communication.models.sessions.communication_session import CommunicationSession
from rescue.communication.models.sessions.session_envelope import SessionEnvelope
from rescue.communication.models.vocabulary.delivery_disposition import DeliveryDisposition
from rescue.communication.models.vocabulary.delivery_reason import DeliveryReason
from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from rescue.communication.models.vocabulary.recovery_rejection import RecoveryRejection
from rescue.communication.rules.recover_reports import recover_reports


def report(sequence):
    return DecisionReport(
        report_id=f"report-{sequence}",
        envelope=SessionEnvelope("local:ship-1", 1, FlowDirection.OUTBOUND, sequence),
        message_id="message-1",
        delivery_id="delivery-1",
        mission_id=None,
        disposition=next(iter(DeliveryDisposition)),
        reason=next(iter(DeliveryReason)),
        mission_sequence=None,
        after_mission_sequence=0,
    )


def session(issued=5, **overrides):
    fields = {
        "session_id": "local:ship-1",
        "version": 1,
        "next_inbound": 1,
        "next_outbound": issued + 1,
        "reports": tuple(report(n) for n in range(1, issued + 1)),
        "gaps": (),
        "outstanding_recovery": None,
    }
    return CommunicationSession(**(fields | overrides))


def request(**overrides):
    fields = {"session_id": "local:ship-1", "version": 1, "from_sequence": 2, "count": 3}
    return RecoveryRequest(**(fields | overrides))


class RecoverReportsTests(unittest.TestCase):
    def test_returns_the_original_reports_in_order_then_a_control(self):
        current = session()
        result = recover_reports(current, request())
        self.assertEqual(len(result), 4)
        for position, original in enumerate(current.reports[1:4]):
            self.assertIs(result[position], original)
        self.assertEqual(result[-1], SequenceControl("local:ship-1", 1, FlowDirection.OUTBOUND, 6))

    def test_a_stale_version_is_refused(self):
        self.assertIs(
            recover_reports(session(), request(version=2)), RecoveryRejection.STALE_SESSION
        )

    def test_an_outstanding_recovery_is_refused(self):
        current = session(outstanding_recovery=request())
        self.assertIs(recover_reports(current, request()), RecoveryRejection.RECOVERY_IN_PROGRESS)

    def test_zero_and_negative_counts_are_refused(self):
        for count in (0, -1):
            self.assertIs(
                recover_reports(session(), request(count=count)), RecoveryRejection.RECOVERY_LIMIT
            )

    def test_one_thousand_is_allowed_and_one_thousand_one_is_refused(self):
        current = session(issued=1001)
        self.assertEqual(len(recover_reports(current, request(from_sequence=1, count=1000))), 1001)
        self.assertIs(
            recover_reports(current, request(from_sequence=1, count=1001)),
            RecoveryRejection.RECOVERY_LIMIT,
        )

    def test_a_range_past_the_last_issued_report_is_refused(self):
        self.assertIs(
            recover_reports(session(), request(from_sequence=4, count=3)),
            RecoveryRejection.RECOVERY_OUT_OF_RANGE,
        )

    def test_the_last_issued_report_is_in_range(self):
        self.assertEqual(len(recover_reports(session(), request(from_sequence=5, count=1))), 2)

    def test_a_stale_version_wins_over_every_other_check(self):
        current = session(outstanding_recovery=request())
        self.assertIs(
            recover_reports(current, request(version=2, count=0)), RecoveryRejection.STALE_SESSION
        )

    def test_an_outstanding_recovery_wins_over_limit_and_range(self):
        current = session(outstanding_recovery=request())
        self.assertIs(
            recover_reports(current, request(from_sequence=9, count=2000)),
            RecoveryRejection.RECOVERY_IN_PROGRESS,
        )

    def test_the_limit_wins_over_the_range(self):
        self.assertIs(
            recover_reports(session(), request(from_sequence=1, count=2000)),
            RecoveryRejection.RECOVERY_LIMIT,
        )

    def test_the_session_is_not_changed(self):
        current = session()
        before = (current.next_inbound, current.next_outbound, current.reports, current.gaps)
        recover_reports(current, request())
        recover_reports(current, request(count=0))
        self.assertEqual(
            before, (current.next_inbound, current.next_outbound, current.reports, current.gaps)
        )
        self.assertIsNone(current.outstanding_recovery)
