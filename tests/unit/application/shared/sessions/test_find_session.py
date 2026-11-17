"""find_session tests."""

import unittest

from rescue.application.shared.find_session import find_session
from rescue.communication.models.sessions.communication_session import CommunicationSession
from rescue.market.models.b3_market import B3Market
from rescue.state import RunState


class FindSessionTests(unittest.TestCase):
    """find_session returns the stored session for an id, or None.

    What: looks a session up in the run's session index.
    When called: by tests of the shared lookup.
    Why: the response and inbound services treat a missing session as a first contact.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def setUp(self):
        self.session = CommunicationSession(
            session_id="local:ship-1",
            version=1,
            next_inbound=1,
            next_outbound=1,
            reports=(),
            gaps=(),
            outstanding_recovery=None,
        )
        self.market = B3Market("MARKET-1")

    def test_returns_the_stored_session(self):
        state = RunState("RUN-1", "CENTRAL-1", self.market, session_index=(self.session,))
        self.assertIs(find_session(state, "local:ship-1"), self.session)

    def test_returns_none_for_an_unknown_session(self):
        state = RunState("RUN-1", "CENTRAL-1", self.market)
        self.assertIsNone(find_session(state, "local:ship-1"))
