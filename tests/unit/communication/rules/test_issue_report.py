"""Issue report rule tests."""

import unittest

from rescue.communication.models.sessions.communication_session import CommunicationSession
from rescue.communication.models.vocabulary.delivery_disposition import DeliveryDisposition
from rescue.communication.models.vocabulary.delivery_reason import DeliveryReason
from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from rescue.communication.rules.issue_report import issue_report


def fresh_session():
    return CommunicationSession("local:ship-1", 1, 1, 1, (), (), None)


def issue(session, n, mission_sequence=1, after=0):
    return issue_report(
        session,
        report_id=f"report-{n}",
        message_id=f"message-{n}",
        delivery_id=f"delivery-{n}",
        mission_id="mission-1",
        disposition=DeliveryDisposition.APPLIED,
        reason=DeliveryReason.RESPONSE_APPLIED,
        mission_sequence=mission_sequence,
        after_mission_sequence=after,
    )


class IssueReportTests(unittest.TestCase):
    def test_builds_outbound_envelope_and_appends_report(self):
        session, report = issue(fresh_session(), 1)
        self.assertEqual(
            (report.envelope.session_id, report.envelope.version, report.envelope.direction),
            ("local:ship-1", 1, FlowDirection.OUTBOUND),
        )
        self.assertEqual(report.envelope.sequence, 1)
        self.assertEqual(session.reports, (report,))
        self.assertEqual(session.next_outbound, 2)
        self.assertEqual(report.message_id, "message-1")

    def test_two_issues_give_sequences_one_and_two(self):
        first, _ = issue(fresh_session(), 1)
        second, report = issue(first, 2, mission_sequence=2, after=1)
        self.assertEqual([r.envelope.sequence for r in second.reports], [1, 2])
        self.assertEqual(report.envelope.sequence, 2)
        self.assertEqual(second.next_outbound, 3)

    def test_input_session_is_unchanged(self):
        before = fresh_session()
        issue(before, 1)
        self.assertEqual(before, fresh_session())
        self.assertEqual(before.reports, ())
        self.assertEqual(before.next_outbound, 1)
