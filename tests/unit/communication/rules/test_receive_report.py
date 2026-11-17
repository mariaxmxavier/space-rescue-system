"""Ship-side report receipt rule tests."""

import unittest

from rescue.communication.models.recovery.decision_report import DecisionReport
from rescue.communication.models.recovery.report_cursor import ReportCursor
from rescue.communication.models.sessions.session_envelope import SessionEnvelope
from rescue.communication.models.vocabulary.delivery_disposition import DeliveryDisposition
from rescue.communication.models.vocabulary.delivery_reason import DeliveryReason
from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from rescue.communication.rules.receive_report import receive_report


def report(sequence):
    return DecisionReport(
        report_id=f"report-{sequence}",
        envelope=SessionEnvelope(
            session_id="local:ship-1",
            version=1,
            direction=FlowDirection.OUTBOUND,
            sequence=sequence,
        ),
        message_id=f"message-{sequence}",
        delivery_id=f"delivery-{sequence}",
        mission_id=None,
        disposition=DeliveryDisposition.REJECTED,
        reason=DeliveryReason.UNKNOWN_REQUEST,
        mission_sequence=None,
        after_mission_sequence=0,
    )


def cursor(next_expected=1, buffered=()):
    return ReportCursor("local:ship-1", 1, next_expected, tuple(buffered))


class ReceiveReportTests(unittest.TestCase):
    def test_expected_report_is_delivered(self):
        new, delivered, gap = receive_report(cursor(), report(1))
        self.assertEqual(delivered, (report(1),))
        self.assertEqual(new, cursor(2))
        self.assertIsNone(gap)

    def test_early_report_is_buffered_with_gap(self):
        new, delivered, gap = receive_report(cursor(), report(2))
        self.assertEqual(delivered, ())
        self.assertEqual(new, cursor(1, [report(2)]))
        self.assertEqual(gap, (1, 1))

    def test_worked_example_buffered_report_drains_in_order(self):
        buffered, _, _ = receive_report(cursor(), report(2))
        new, delivered, gap = receive_report(buffered, report(1))
        self.assertEqual(delivered, (report(1), report(2)))
        self.assertEqual(new, cursor(3))
        self.assertIsNone(gap)

    def test_gap_is_leading_missing_run_before_first_buffered(self):
        start = cursor(1, [report(3)])
        new, delivered, gap = receive_report(start, report(5))
        self.assertEqual(gap, (1, 2))
        self.assertEqual(new.buffered, (report(3), report(5)))
        self.assertEqual(delivered, ())

    def test_gap_ends_at_arriving_report_when_it_is_earliest(self):
        start = cursor(1, [report(5)])
        _, _, gap = receive_report(start, report(3))
        self.assertEqual(gap, (1, 2))

    def test_drain_stops_at_next_gap(self):
        start = cursor(1, [report(2), report(4)])
        new, delivered, gap = receive_report(start, report(1))
        self.assertEqual(delivered, (report(1), report(2)))
        self.assertEqual(new, cursor(3, [report(4)]))
        self.assertIsNone(gap)

    def test_old_report_has_no_effect(self):
        start = cursor(3)
        self.assertEqual(receive_report(start, report(2)), (start, (), None))

    def test_buffered_report_has_no_effect(self):
        start = cursor(1, [report(2)])
        self.assertEqual(receive_report(start, report(2)), (start, (), None))
