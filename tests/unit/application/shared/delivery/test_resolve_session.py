"""resolve_session tests."""

import unittest

from rescue.application.shared.delivery.classify_response import classify_response
from rescue.application.shared.delivery.normalise_response import normalise_response
from rescue.application.shared.delivery.resolve_session import resolve_session
from rescue.communication.models import FlowDirection, SessionEnvelope
from rescue.communication.models.sessions.communication_session import CommunicationSession
from rescue.values import DomainValidationError
from tests.unit.application.shared.delivery.support import response, state_with_request


def classified(command, state):
    context, _ = classify_response(state, normalise_response(command))
    return context


class ResolveSessionTests(unittest.TestCase):
    """resolve_session picks the envelope and accepts it on the session.

    What: defaults the envelope to local:<ship>, accepts the inbound and flags a stale one.
    When called: by tests of the third delivery step.
    Why: the default session changes the session index but never an outcome.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def test_creates_the_default_local_session_when_the_envelope_is_absent(self):
        command = response()
        state = state_with_request()
        resolved, rejection = resolve_session(state, classified(command, state), command)
        self.assertIsNone(rejection)
        self.assertEqual(resolved.envelope.session_id, "local:ship-1")
        self.assertEqual(resolved.envelope.version, 1)
        self.assertEqual(resolved.session.session_id, "local:ship-1")
        self.assertEqual(resolved.verdict, "execute")

    def test_a_lost_delivery_has_no_session(self):
        command = response(received_at=None)
        state = state_with_request()
        resolved, rejection = resolve_session(state, classified(command, state), command)
        self.assertIsNone(rejection)
        self.assertIsNone(resolved.session)
        self.assertIsNone(resolved.envelope)

    def test_stale_returns_rejected_stale_session(self):
        session = CommunicationSession(
            session_id="local:ship-1",
            version=2,
            next_inbound=1,
            next_outbound=1,
            reports=(),
            gaps=(),
            outstanding_recovery=None,
        )
        state = state_with_request(session_index=(session,))
        envelope = SessionEnvelope("local:ship-1", 1, FlowDirection.INBOUND, 1)
        command = response(envelope=envelope)
        resolved, rejection = resolve_session(state, classified(command, state), command)
        self.assertEqual(resolved.verdict, "stale")
        self.assertEqual(rejection.status, "rejected")
        self.assertEqual(rejection.reason, "stale_session")

    def test_a_non_envelope_is_rejected(self):
        command = response(envelope="bad")
        state = state_with_request()
        with self.assertRaisesRegex(DomainValidationError, "envelope must be a session envelope"):
            resolve_session(state, classified(command, state), command)
