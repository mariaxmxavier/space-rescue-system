"""get_session service tests."""

import unittest
from dataclasses import replace

from rescue.application.services.communication.get_session import get_session
from rescue.communication.models.sessions.communication_session import CommunicationSession
from tests.unit.application.services.fakes import FakeStore, empty_state


def session():
    return CommunicationSession("local:ship-1", 1, 1, 1, (), (), None)


class GetSessionTests(unittest.TestCase):
    """get_session returns one stored session or names why it cannot.

    What: looks a session up by id without changing the run.
    When called: by tests of the get_session service.
    Why: an absent session is a named rejection, so a typo is not read as an empty session.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
    """

    def setUp(self):
        self.current = session()
        self.store = FakeStore(replace(empty_state(), session_index=(self.current,)))

    def test_returns_the_stored_session(self):
        result = get_session("local:ship-1", store=self.store)
        self.assertEqual(result.status, "applied")
        self.assertIs(result.value, self.current)

    def test_unknown_session_is_rejected(self):
        result = get_session("local:ship-2", store=self.store)
        self.assertEqual((result.status, result.reason), ("rejected", "unknown_session"))

    def test_invalid_id_is_rejected_as_invalid_input(self):
        result = get_session("", store=self.store)
        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))

    def test_nothing_is_published_on_rejection(self):
        before = self.store.state
        get_session("local:ship-2", store=self.store)
        self.assertIs(self.store.state, before)
