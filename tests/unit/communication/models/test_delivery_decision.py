"""Delivery decision tests."""

import unittest

from rescue.communication.models.deliveries.delivery_decision import DeliveryDecision
from rescue.communication.models.vocabulary.delivery_disposition import DeliveryDisposition
from rescue.communication.models.vocabulary.delivery_reason import DeliveryReason
from rescue.values import DomainValidationError


def _decision(**overrides):
    fields = {
        "disposition": DeliveryDisposition.APPLIED,
        "reason": DeliveryReason.RESPONSE_APPLIED,
        "action": "apply",
        "result_status": "applied",
        "result_reason": None,
    }
    return DeliveryDecision(**{**fields, **overrides})


class DeliveryDecisionTest(unittest.TestCase):
    def test_builds_a_recording_decision(self):
        decision = _decision()
        self.assertEqual(decision.action, "apply")
        self.assertIs(decision.disposition, DeliveryDisposition.APPLIED)

    def test_none_action_has_no_disposition_and_keeps_its_result_reason(self):
        decision = _decision(
            disposition=None,
            reason=None,
            action="none",
            result_status="rejected",
            result_reason=DeliveryReason.IDENTITY_CONFLICT,
        )
        self.assertIsNone(decision.disposition)

    def test_every_action_is_accepted(self):
        for action in ("record", "expire_then_record", "apply"):
            self.assertEqual(_decision(action=action).action, action)

    def test_unknown_action_is_rejected(self):
        with self.assertRaises(DomainValidationError):
            _decision(action="drop")

    def test_none_action_with_disposition_or_reason_is_rejected(self):
        with self.assertRaises(DomainValidationError):
            _decision(action="none", reason=None)
        with self.assertRaises(DomainValidationError):
            _decision(action="none", disposition=None)

    def test_recording_action_requires_disposition_and_reason(self):
        with self.assertRaises(DomainValidationError):
            _decision(disposition=None)
        with self.assertRaises(DomainValidationError):
            _decision(reason=None)

    def test_unknown_result_status_is_rejected(self):
        with self.assertRaises(DomainValidationError):
            _decision(result_status="late")

    def test_result_reason_accepts_late_and_reason_values_only(self):
        self.assertEqual(_decision(result_reason="late").result_reason, "late")
        reason = _decision(result_reason=DeliveryReason.CLOSED_REQUEST).result_reason
        self.assertIs(reason, DeliveryReason.CLOSED_REQUEST)
        with self.assertRaises(DomainValidationError):
            _decision(result_reason="bogus")

    def test_decision_is_immutable(self):
        with self.assertRaises(AttributeError):
            _decision().action = "record"
