"""synchronise_inbound service tests."""

import unittest
from dataclasses import replace

from rescue.application.contracts import SynchroniseInbound
from rescue.application.services.communication.synchronise_inbound import synchronise_inbound
from rescue.communication.models.sessions.communication_session import CommunicationSession
from rescue.communication.models.sessions.not_applied import NotApplied
from tests.unit.application.services.fakes import FakeStore, empty_state


def session():
    return CommunicationSession("local:ship-1", 1, 3, 1, (), (), None)


def command(**overrides):
    fields = {"session_id": "local:ship-1", "version": 1, "next_sequence": 6}
    return SynchroniseInbound(**(fields | overrides))


class SynchroniseInboundTests(unittest.TestCase):
    """synchronise_inbound advances the expected inbound number or rejects.

    What: applies the synchronise rule and publishes the session with any gap it recorded.
    When called: by tests of the synchronise_inbound service.
    Why: a refusal publishes nothing, so counters and gaps stay as they were.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
    """

    def setUp(self):
        self.store = FakeStore(replace(empty_state(), session_index=(session(),)))
        self.before = self.store.state

    def test_a_higher_number_publishes_the_session_with_a_gap(self):
        result = synchronise_inbound(command(), store=self.store)
        self.assertEqual(result.status, "applied")
        self.assertEqual(result.value.next_inbound, 6)
        self.assertEqual(result.value.gaps, (NotApplied("local:ship-1", 1, 3, 3),))
        self.assertEqual(self.store.state.session_index, (result.value,))

    def test_an_equal_number_publishes_the_session_unchanged(self):
        result = synchronise_inbound(command(next_sequence=3), store=self.store)
        self.assertEqual(result.status, "applied")
        self.assertEqual(result.value, session())
        self.assertEqual(self.store.state.session_index, (session(),))

    def test_unknown_session_is_rejected(self):
        result = synchronise_inbound(command(session_id="local:ship-2"), store=self.store)
        self.assertEqual((result.status, result.reason), ("rejected", "unknown_session"))
        self.assertIs(self.store.state, self.before)

    def test_a_rule_refusal_carries_its_reason(self):
        for changed, reason in (
            ({"version": 2}, "stale_session"),
            ({"next_sequence": 2}, "sequence_rewind"),
        ):
            with self.subTest(reason=reason):
                result = synchronise_inbound(command(**changed), store=self.store)
                self.assertEqual((result.status, result.reason), ("rejected", reason))
                self.assertIs(self.store.state, self.before)

    def test_invalid_input_is_rejected(self):
        result = synchronise_inbound(command(next_sequence="six"), store=self.store)
        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))
        self.assertIs(self.store.state, self.before)
