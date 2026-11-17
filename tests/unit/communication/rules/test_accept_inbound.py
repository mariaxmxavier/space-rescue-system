"""One test per session row of accept_inbound."""

import unittest

from rescue.communication.models.sessions.communication_session import CommunicationSession
from rescue.communication.models.sessions.not_applied import NotApplied
from rescue.communication.models.sessions.session_envelope import SessionEnvelope
from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from rescue.communication.rules.accept_inbound import accept_inbound
from rescue.values import DomainValidationError


def envelope(sequence, version=1, direction=FlowDirection.INBOUND):
    return SessionEnvelope("s1", version, direction, sequence)


def session(version=1, next_inbound=1, gaps=()):
    return CommunicationSession("s1", version, next_inbound, 1, (), gaps, None)


class AcceptInboundTest(unittest.TestCase):
    def test_no_session_creates_one_and_executes_first_sequence(self):
        got = accept_inbound(None, envelope(1, version=2))
        self.assertEqual(got, (session(version=2, next_inbound=2), None, "execute"))

    def test_no_session_with_skipped_first_sequence_records_gap(self):
        new, gap, verdict = accept_inbound(None, envelope(3))
        self.assertEqual(gap, NotApplied("s1", 1, 1, 2))
        self.assertEqual((new.next_inbound, verdict), (4, "execute"))

    def test_higher_version_resets_session(self):
        old = session(version=1, next_inbound=5, gaps=(NotApplied("s1", 1, 2, 1),))
        got = accept_inbound(old, envelope(1, version=2))
        self.assertEqual(got, (session(version=2, next_inbound=2), None, "execute"))

    def test_lower_version_is_stale_and_unchanged(self):
        old = session(version=3, next_inbound=4)
        self.assertEqual(accept_inbound(old, envelope(4, version=2)), (old, None, "stale"))

    def test_expected_sequence_executes(self):
        got = accept_inbound(session(next_inbound=4), envelope(4))
        self.assertEqual(got, (session(next_inbound=5), None, "execute"))

    def test_skipped_sequence_records_gap_and_executes(self):
        new, gap, verdict = accept_inbound(session(next_inbound=2), envelope(5))
        self.assertEqual(gap, NotApplied("s1", 1, 2, 3))
        self.assertEqual(new, session(next_inbound=6, gaps=(gap,)))
        self.assertEqual(verdict, "execute")

    def test_old_sequence_is_duplicate_and_unchanged(self):
        old = session(next_inbound=4)
        self.assertEqual(accept_inbound(old, envelope(3)), (old, None, "duplicate"))

    def test_outbound_envelope_is_rejected(self):
        with self.assertRaises(DomainValidationError):
            accept_inbound(session(), envelope(1, direction=FlowDirection.OUTBOUND))


if __name__ == "__main__":
    unittest.main()
