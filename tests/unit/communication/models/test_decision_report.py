"""Decision report value tests."""

import dataclasses
import unittest

from rescue.communication.models.recovery.decision_report import DecisionReport
from rescue.communication.models.sessions.session_envelope import SessionEnvelope
from rescue.communication.models.vocabulary.delivery_disposition import DeliveryDisposition
from rescue.communication.models.vocabulary.delivery_reason import DeliveryReason
from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from rescue.values import DomainValidationError


def outbound_envelope(**overrides):
    fields = {
        "session_id": "local:ship-1",
        "version": 1,
        "direction": FlowDirection.OUTBOUND,
        "sequence": 1,
    }
    return SessionEnvelope(**(fields | overrides))


def decision_report(**overrides):
    fields = {
        "report_id": "report-1",
        "envelope": outbound_envelope(),
        "message_id": "message-1",
        "delivery_id": "delivery-1",
        "mission_id": "mission-1",
        "disposition": DeliveryDisposition.APPLIED,
        "reason": DeliveryReason.RESPONSE_APPLIED,
        "mission_sequence": 1,
        "after_mission_sequence": 0,
    }
    return DecisionReport(**(fields | overrides))


class DecisionReportTests(unittest.TestCase):
    def test_keeps_its_identity_and_mission_order_fields(self):
        report = decision_report(mission_sequence=3, after_mission_sequence=2)
        self.assertEqual(report.report_id, "report-1")
        self.assertEqual(report.message_id, "message-1")
        self.assertEqual(report.delivery_id, "delivery-1")
        self.assertEqual(report.mission_id, "mission-1")
        self.assertIs(report.disposition, DeliveryDisposition.APPLIED)
        self.assertIs(report.reason, DeliveryReason.RESPONSE_APPLIED)
        self.assertEqual(report.mission_sequence, 3)
        self.assertEqual(report.after_mission_sequence, 2)
        self.assertEqual(report.envelope.sequence, 1)

    def test_unknown_request_has_no_mission_and_no_order_number(self):
        report = decision_report(
            mission_id=None,
            disposition=DeliveryDisposition.REJECTED,
            reason=DeliveryReason.UNKNOWN_REQUEST,
            mission_sequence=None,
            after_mission_sequence=0,
        )
        self.assertIsNone(report.mission_id)
        self.assertIsNone(report.mission_sequence)
        self.assertEqual(report.after_mission_sequence, 0)

    def test_rejected_decision_on_known_mission_keeps_the_number_it_was_evaluated_after(self):
        report = decision_report(
            disposition=DeliveryDisposition.REJECTED,
            reason=DeliveryReason.CLOSED_REQUEST,
            mission_sequence=None,
            after_mission_sequence=4,
        )
        self.assertIsNone(report.mission_sequence)
        self.assertEqual(report.after_mission_sequence, 4)

    def test_blank_or_non_string_identifiers_are_rejected(self):
        for field_name in ("report_id", "message_id", "delivery_id"):
            for bad_value in ("", "   ", None, 7):
                with self.subTest(field=field_name, value=bad_value):
                    with self.assertRaisesRegex(
                        DomainValidationError, "identifier must be a nonblank string"
                    ):
                        decision_report(**{field_name: bad_value})

    def test_mission_id_may_be_absent_but_must_be_nonblank_when_given(self):
        report = decision_report(mission_id=None, mission_sequence=None, after_mission_sequence=0)
        self.assertIsNone(report.mission_id)
        for bad_value in ("", "  ", 7):
            with self.subTest(mission_id=bad_value):
                with self.assertRaisesRegex(
                    DomainValidationError, "identifier must be a nonblank string"
                ):
                    decision_report(mission_id=bad_value)

    def test_envelope_must_be_an_outbound_session_envelope(self):
        inbound = outbound_envelope(direction=FlowDirection.INBOUND)
        for envelope in (inbound, None, "outbound"):
            with self.subTest(envelope=envelope):
                with self.assertRaisesRegex(
                    DomainValidationError,
                    "decision report envelope must be an outbound session envelope",
                ):
                    decision_report(envelope=envelope)

    def test_disposition_is_always_a_known_disposition(self):
        self.assertIs(decision_report(disposition="late").disposition, DeliveryDisposition.LATE)
        for bad_value in (None, "", "accepted"):
            with self.subTest(disposition=bad_value):
                with self.assertRaisesRegex(
                    DomainValidationError, "decision report disposition must be a known disposition"
                ):
                    decision_report(disposition=bad_value)

    def test_reason_must_be_a_known_reason(self):
        self.assertIs(
            decision_report(reason="unknown_mission").reason, DeliveryReason.UNKNOWN_MISSION
        )
        for bad_value in (None, "", "because"):
            with self.subTest(reason=bad_value):
                with self.assertRaisesRegex(
                    DomainValidationError, "decision report reason must be a known reason"
                ):
                    decision_report(reason=bad_value)

    def test_after_mission_sequence_must_be_a_nonnegative_integer(self):
        for bad_value in (-1, True, 1.0, "0"):
            with self.subTest(after_mission_sequence=bad_value):
                with self.assertRaisesRegex(
                    DomainValidationError, "quantity must be a nonnegative integer"
                ):
                    decision_report(after_mission_sequence=bad_value, mission_sequence=None)

    def test_mission_sequence_must_be_none_or_follow_the_previous_number(self):
        self.assertEqual(
            decision_report(mission_sequence=5, after_mission_sequence=4).mission_sequence, 5
        )
        for bad_value in (4, 6):
            with self.subTest(mission_sequence=bad_value):
                with self.assertRaisesRegex(
                    DomainValidationError,
                    "mission_sequence must be None or after_mission_sequence \\+ 1",
                ):
                    decision_report(mission_sequence=bad_value, after_mission_sequence=4)

    def test_mission_sequence_must_be_a_positive_integer_not_a_bool(self):
        for bad_value in (0, True):
            with self.subTest(mission_sequence=bad_value):
                with self.assertRaisesRegex(
                    DomainValidationError, "quantity must be a positive integer"
                ):
                    decision_report(mission_sequence=bad_value, after_mission_sequence=0)

    def test_report_without_a_mission_cannot_carry_mission_order_numbers(self):
        for overrides in (
            {"mission_sequence": 1, "after_mission_sequence": 0},
            {"mission_sequence": None, "after_mission_sequence": 2},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaisesRegex(DomainValidationError, "without a mission"):
                    decision_report(mission_id=None, **overrides)

    def test_report_is_immutable(self):
        report = decision_report()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            report.reason = DeliveryReason.INVALID_INPUT


if __name__ == "__main__":
    unittest.main()
