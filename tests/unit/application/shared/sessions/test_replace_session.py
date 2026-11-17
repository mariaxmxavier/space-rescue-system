"""replace_session tests."""

import unittest

from rescue.application.shared.replace_session import replace_session
from rescue.communication.models.sessions.communication_session import CommunicationSession
from rescue.market.models.b3_market import B3Market
from rescue.state import RunState


def session(version=1):
    return CommunicationSession(
        session_id="local:ship-1",
        version=version,
        next_inbound=1,
        next_outbound=1,
        reports=(),
        gaps=(),
        outstanding_recovery=None,
    )


class ReplaceSessionTests(unittest.TestCase):
    """replace_session appends a new session and replaces a known one by id.

    What: returns a new state whose session index holds one value per id.
    When called: by tests of the shared writer.
    Why: a newer session version must replace the old one, never sit beside it.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def setUp(self):
        self.state = RunState("RUN-1", "CENTRAL-1", B3Market("MARKET-1"))

    def test_appends_a_new_session(self):
        first = session()
        self.assertEqual(replace_session(self.state, first).session_index, (first,))

    def test_replaces_a_known_session_by_id(self):
        state = replace_session(self.state, session(version=1))
        newer = session(version=2)
        self.assertEqual(replace_session(state, newer).session_index, (newer,))
