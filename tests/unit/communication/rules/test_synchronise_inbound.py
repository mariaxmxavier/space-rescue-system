"""One test per row of synchronise_inbound."""

import unittest

from rescue.communication.models.recovery.sequence_control import SequenceControl
from rescue.communication.models.sessions.communication_session import CommunicationSession
from rescue.communication.models.sessions.not_applied import NotApplied
from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from rescue.communication.models.vocabulary.recovery_rejection import RecoveryRejection
from rescue.communication.rules.synchronise_inbound import synchronise_inbound
from rescue.values import DomainValidationError


def session(next_inbound=3, version=2):
    return CommunicationSession("local:ship-1", version, next_inbound, 1, (), (), None)


def control(next_sequence, version=2, direction=FlowDirection.INBOUND):
    return SequenceControl("local:ship-1", version, direction, next_sequence)


class SynchroniseInboundTest(unittest.TestCase):
    def test_row_1_version_mismatch_is_stale_session(self):
        for version in (1, 3):
            got = synchronise_inbound(session(), control(5, version=version))
            self.assertIs(got, RecoveryRejection.STALE_SESSION)

    def test_row_2_outbound_control_is_a_domain_error(self):
        with self.assertRaises(DomainValidationError):
            synchronise_inbound(session(), control(5, direction=FlowDirection.OUTBOUND))

    def test_row_3_advance_records_the_skipped_range(self):
        got = synchronise_inbound(session(), control(7))
        notice = NotApplied("local:ship-1", 2, 3, 4)
        self.assertEqual(
            got, (session(7).__class__("local:ship-1", 2, 7, 1, (), (notice,), None), notice)
        )

    def test_row_4_equal_leaves_the_session_unchanged(self):
        current = session()
        self.assertEqual(synchronise_inbound(current, control(3)), (current, None))

    def test_row_5_rewind_is_rejected(self):
        self.assertIs(synchronise_inbound(session(), control(2)), RecoveryRejection.SEQUENCE_REWIND)
