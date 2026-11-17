"""Report cursor value tests."""

import dataclasses
import unittest

from rescue.communication.models.recovery.decision_report import DecisionReport
from rescue.communication.models.recovery.report_cursor import ReportCursor
from rescue.communication.models.sessions.session_envelope import SessionEnvelope
from rescue.communication.models.vocabulary.delivery_disposition import DeliveryDisposition
from rescue.communication.models.vocabulary.delivery_reason import DeliveryReason
from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from rescue.values import DomainValidationError


def report(sequence, session_id="local:ship-1", version=1):
    return DecisionReport(
        report_id=f"report-{sequence}",
        envelope=SessionEnvelope(
            session_id=session_id,
            version=version,
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


def cursor(**overrides):
    fields = {"session_id": "local:ship-1", "version": 1, "next_expected": 1, "buffered": ()}
    return ReportCursor(**(fields | overrides))


class ReportCursorTests(unittest.TestCase):
    def test_keeps_its_fields_and_buffered_reports(self):
        value = cursor(next_expected=2, buffered=[report(3), report(5)])
        self.assertEqual(value.session_id, "local:ship-1")
        self.assertEqual(value.version, 1)
        self.assertEqual(value.next_expected, 2)
        self.assertEqual(value.buffered, (report(3), report(5)))
        self.assertIsInstance(value.buffered, tuple)

    def test_blank_session_id_is_rejected(self):
        for bad_value in ("", "  ", None, 7):
            with self.subTest(session_id=bad_value):
                with self.assertRaisesRegex(
                    DomainValidationError, "identifier must be a nonblank string"
                ):
                    cursor(session_id=bad_value)

    def test_version_and_next_expected_must_be_positive_integers(self):
        for field_name in ("version", "next_expected"):
            for bad_value in (0, -1, True, 1.0):
                with self.subTest(field=field_name, value=bad_value):
                    with self.assertRaisesRegex(
                        DomainValidationError, "quantity must be a positive integer"
                    ):
                        cursor(**{field_name: bad_value})

    def test_buffered_must_hold_decision_reports(self):
        with self.assertRaisesRegex(DomainValidationError, "decision reports"):
            cursor(buffered=("report",))

    def test_buffered_must_be_sorted_without_duplicates(self):
        for buffered in ((report(4), report(3)), (report(3), report(3))):
            with self.subTest(sequences=[r.envelope.sequence for r in buffered]):
                with self.assertRaisesRegex(DomainValidationError, "strictly increasing"):
                    cursor(buffered=buffered)

    def test_buffered_sequences_must_be_after_next_expected(self):
        for sequence in (1, 2):
            with self.subTest(sequence=sequence):
                with self.assertRaisesRegex(DomainValidationError, "after next_expected"):
                    cursor(next_expected=2, buffered=(report(sequence),))

    def test_buffered_must_share_the_session_id_and_version(self):
        for other in (report(3, session_id="local:ship-2"), report(3, version=2)):
            with self.subTest(other=other.envelope):
                with self.assertRaisesRegex(DomainValidationError, "same session and version"):
                    cursor(buffered=(other,))

    def test_cursor_is_immutable(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            cursor().next_expected = 2


if __name__ == "__main__":
    unittest.main()
