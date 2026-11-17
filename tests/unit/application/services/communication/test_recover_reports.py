"""recover_reports service tests."""

import unittest
from dataclasses import replace

from rescue.application.contracts import RecoverReports
from rescue.application.services.communication.recover_reports import recover_reports
from rescue.communication.models.recovery.decision_report import DecisionReport
from rescue.communication.models.recovery.recovery_request import RecoveryRequest
from rescue.communication.models.recovery.sequence_control import SequenceControl
from rescue.communication.models.sessions.communication_session import CommunicationSession
from rescue.communication.models.sessions.session_envelope import SessionEnvelope
from rescue.communication.models.vocabulary.delivery_disposition import DeliveryDisposition
from rescue.communication.models.vocabulary.delivery_reason import DeliveryReason
from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from tests.unit.application.services.fakes import FakeStore, empty_state


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


def session(**overrides):
    fields = {
        "session_id": "local:ship-1",
        "version": 1,
        "next_inbound": 1,
        "next_outbound": 4,
        "reports": tuple(report(n) for n in range(1, 4)),
        "gaps": (),
        "outstanding_recovery": None,
    }
    return CommunicationSession(**(fields | overrides))


def command(**overrides):
    fields = {"session_id": "local:ship-1", "version": 1, "from_sequence": 2, "count": 2}
    return RecoverReports(**(fields | overrides))


class RecoverReportsTests(unittest.TestCase):
    """recover_reports replays retained reports or rejects with a named reason.

    What: looks up the session and asks the recovery rule for the requested range.
    When called: by tests of the recover_reports service.
    Why: recovery only reads, so every outcome leaves the run state as it was.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
    """

    def setUp(self):
        self.current = session()
        self.store = FakeStore(replace(empty_state(), session_index=(self.current,)))
        self.before = self.store.state

    def test_replays_the_original_reports_then_a_control(self):
        result = recover_reports(command(), store=self.store)
        self.assertEqual(result.status, "applied")
        self.assertIs(result.value[0], self.current.reports[1])
        self.assertIs(result.value[1], self.current.reports[2])
        self.assertEqual(
            result.value[2], SequenceControl("local:ship-1", 1, FlowDirection.OUTBOUND, 4)
        )
        self.assertIs(self.store.state, self.before)

    def test_unknown_session_is_rejected(self):
        result = recover_reports(command(session_id="local:ship-2"), store=self.store)
        self.assertEqual((result.status, result.reason), ("rejected", "unknown_session"))

    def test_a_rule_refusal_carries_its_reason(self):
        for changed, reason in (
            ({"version": 2}, "stale_session"),
            ({"count": 0}, "recovery_limit"),
            ({"count": 9}, "recovery_out_of_range"),
        ):
            with self.subTest(reason=reason):
                result = recover_reports(command(**changed), store=self.store)
                self.assertEqual((result.status, result.reason), ("rejected", reason))

    def test_an_outstanding_recovery_is_refused(self):
        outstanding = RecoveryRequest("local:ship-1", 1, 1, 1)
        store = FakeStore(
            replace(empty_state(), session_index=(session(outstanding_recovery=outstanding),))
        )
        result = recover_reports(command(), store=store)
        self.assertEqual((result.status, result.reason), ("rejected", "recovery_in_progress"))

    def test_a_start_below_one_is_out_of_range(self):
        for start in (0, -3):
            with self.subTest(start=start):
                result = recover_reports(command(from_sequence=start), store=self.store)
                self.assertEqual(
                    (result.status, result.reason), ("rejected", "recovery_out_of_range")
                )

    def test_a_stale_version_wins_over_a_start_below_one(self):
        result = recover_reports(command(version=2, from_sequence=0), store=self.store)
        self.assertEqual((result.status, result.reason), ("rejected", "stale_session"))

    def test_invalid_input_is_rejected(self):
        result = recover_reports(command(session_id=""), store=self.store)
        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))

    def test_nothing_is_published_on_rejection(self):
        recover_reports(command(version=2), store=self.store)
        self.assertIs(self.store.state, self.before)
