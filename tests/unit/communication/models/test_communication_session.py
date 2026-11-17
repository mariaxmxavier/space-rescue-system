"""Communication session tests."""

import unittest
from dataclasses import FrozenInstanceError

from rescue.communication.models.recovery.decision_report import DecisionReport
from rescue.communication.models.recovery.recovery_request import RecoveryRequest
from rescue.communication.models.sessions.communication_session import CommunicationSession
from rescue.communication.models.sessions.not_applied import NotApplied
from rescue.communication.models.sessions.session_envelope import SessionEnvelope
from rescue.communication.models.vocabulary.delivery_disposition import DeliveryDisposition
from rescue.communication.models.vocabulary.delivery_reason import DeliveryReason
from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from rescue.values import DomainValidationError


def report(sequence, session_id="local:ship-1", version=1):
    return DecisionReport(
        report_id=f"report-{session_id}-{version}-{sequence}",
        envelope=SessionEnvelope(session_id, version, FlowDirection.OUTBOUND, sequence),
        message_id="message-1",
        delivery_id="delivery-1",
        mission_id=None,
        disposition=next(iter(DeliveryDisposition)),
        reason=next(iter(DeliveryReason)),
        mission_sequence=None,
        after_mission_sequence=0,
    )


def session(**overrides):
    fields = {
        "session_id": "local:ship-1",
        "version": 1,
        "next_inbound": 1,
        "next_outbound": 1,
        "reports": (),
        "gaps": (),
        "outstanding_recovery": None,
    }
    return CommunicationSession(**(fields | overrides))


class CommunicationSessionTests(unittest.TestCase):
    def test_stores_counters_reports_gaps_and_recovery(self):
        gap = NotApplied("local:ship-1", 1, 2, 1)
        ask = RecoveryRequest("local:ship-1", 1, 1, 1)
        current = session(
            next_inbound=4,
            next_outbound=3,
            reports=(report(1), report(2)),
            gaps=(gap,),
            outstanding_recovery=ask,
        )

        self.assertEqual(
            (
                current.next_inbound,
                current.next_outbound,
                current.gaps,
                current.outstanding_recovery,
            ),
            (4, 3, (gap,), ask),
        )
        self.assertEqual(len(current.reports), 2)

    def test_is_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            session().version = 2

    def test_session_id_must_be_nonblank(self):
        with self.assertRaisesRegex(DomainValidationError, "identifier must be a nonblank"):
            session(session_id=" ")

    def test_version_must_be_positive(self):
        with self.assertRaisesRegex(DomainValidationError, "positive integer"):
            session(version=0)

    def test_next_inbound_must_be_at_least_one(self):
        with self.assertRaisesRegex(DomainValidationError, "positive integer"):
            session(next_inbound=0)

    def test_next_outbound_must_be_at_least_one(self):
        with self.assertRaisesRegex(DomainValidationError, "positive integer"):
            session(next_outbound=0)

    def test_reports_must_be_a_tuple(self):
        with self.assertRaisesRegex(DomainValidationError, "reports must be a tuple"):
            session(reports=[])

    def test_reports_must_cover_exactly_the_issued_sequences(self):
        with self.assertRaisesRegex(DomainValidationError, "outbound sequences"):
            session(next_outbound=3, reports=(report(1),))

    def test_reports_must_be_in_order(self):
        with self.assertRaisesRegex(DomainValidationError, "outbound sequences"):
            session(next_outbound=3, reports=(report(2), report(1)))

    def test_reports_must_belong_to_the_session(self):
        with self.assertRaisesRegex(DomainValidationError, "report session"):
            session(next_outbound=2, reports=(report(1, session_id="local:ship-2"),))

    def test_reports_must_match_the_version(self):
        with self.assertRaisesRegex(DomainValidationError, "report session"):
            session(next_outbound=2, reports=(report(1, version=2),))

    def test_reports_must_be_decision_reports(self):
        with self.assertRaisesRegex(DomainValidationError, "decision reports"):
            session(next_outbound=2, reports=("x",))

    def test_gaps_must_be_a_tuple(self):
        with self.assertRaisesRegex(DomainValidationError, "gaps must be a tuple"):
            session(gaps=[])

    def test_gaps_must_be_not_applied_notices(self):
        with self.assertRaisesRegex(DomainValidationError, "not applied notices"):
            session(gaps=("x",))

    def test_gaps_must_match_session_and_version(self):
        with self.assertRaisesRegex(DomainValidationError, "gap session"):
            session(gaps=(NotApplied("local:ship-1", 2, 1, 1),))

    def test_recovery_must_be_a_recovery_request(self):
        with self.assertRaisesRegex(DomainValidationError, "recovery request"):
            session(outstanding_recovery="x")

    def test_recovery_must_match_session_and_version(self):
        with self.assertRaisesRegex(DomainValidationError, "recovery session"):
            session(outstanding_recovery=RecoveryRequest("local:ship-2", 1, 1, 1))
