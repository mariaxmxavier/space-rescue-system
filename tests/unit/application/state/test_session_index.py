"""Run state session index tests."""

import unittest
from dataclasses import FrozenInstanceError

from rescue.application.state import RunState
from rescue.communication.models.sessions.communication_session import CommunicationSession
from rescue.market.models.b3_market import B3Market
from rescue.values import DomainValidationError


def session(session_id="local:ship-1", version=1):
    """Build a session with no traffic, for placing in a run's session index.

    What: a session at its first counters with no reports, gaps or outstanding recovery.
    When called: by the run state tests that need a valid session value.
    Why: index validation depends only on session identity, so an empty session keeps each test about the index.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
    """
    return CommunicationSession(
        session_id=session_id,
        version=version,
        next_inbound=1,
        next_outbound=1,
        reports=(),
        gaps=(),
        outstanding_recovery=None,
    )


def run_state(**overrides):
    """Build a run state with the required fields, adding any overrides.

    What: a run state for one application run with a B3 market and no other state.
    When called: by the run state tests, with the session index as the only override under test.
    Why: each test names only the field it checks, so a default run state must stay valid without a session index.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
    """
    fields = {
        "application_run_id": "RUN-1",
        "central_id": "CENTRAL-1",
        "market": B3Market(market_id="MARKET-RUN-1"),
    }
    return RunState(**(fields | overrides))


class RunStateSessionIndexTests(unittest.TestCase):
    """Run state keeps its session index as an immutable, identity-unique tuple of sessions.

    What: the session index field of the run state and its validation.
    When called: whenever a run state is built or replaced by a transaction.
    Why: sessions are published with the run state, so a mutable or duplicated index would break atomic publication.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
    """

    def test_defaults_to_an_empty_session_index(self):
        self.assertEqual(run_state().session_index, ())

    def test_stores_sessions_as_an_immutable_tuple(self):
        first = session("local:ship-1")
        second = session("local:ship-2")

        state = run_state(session_index=[first, second])

        self.assertEqual(state.session_index, (first, second))
        self.assertIsInstance(state.session_index, tuple)
        with self.assertRaises(FrozenInstanceError):
            state.session_index = ()

    def test_rejects_values_that_are_not_communication_sessions(self):
        with self.assertRaises(DomainValidationError):
            run_state(session_index=("local:ship-1",))
        with self.assertRaises(DomainValidationError):
            run_state(session_index=(session(), {"session_id": "local:ship-2"}))

    def test_rejects_a_string_as_the_session_index(self):
        with self.assertRaises(DomainValidationError):
            run_state(session_index="local:ship-1")

    def test_rejects_two_sessions_with_the_same_session_id(self):
        with self.assertRaises(DomainValidationError):
            run_state(session_index=(session("local:ship-1", 1), session("local:ship-1", 2)))


if __name__ == "__main__":
    unittest.main()
