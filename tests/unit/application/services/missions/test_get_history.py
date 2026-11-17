"""Tests of the get_history service.

What: proves history is read for a known mission and refused for an unknown or malformed query.
When called: by pytest with the application unit tests.
Why: a read must never change the run state, whatever its outcome.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

import unittest

from rescue.application.contracts import RegisterMission
from rescue.application.services.missions.get_history import get_history
from rescue.application.services.missions.register_mission import register_mission
from tests.unit.application.services.fakes import FakeStore, empty_state


class GetHistoryTests(unittest.TestCase):
    def setUp(self):
        self.store = FakeStore(empty_state())
        register_mission(
            RegisterMission(
                mission_id="MISSION-1", station_name="Station A", people_count=5, created_at=0
            ),
            store=self.store,
        )
        self.before = self.store.state

    def test_applies_with_the_mission_history(self):
        result = get_history("MISSION-1", store=self.store)

        self.assertEqual("applied", result.status)
        self.assertEqual((), result.value)
        self.assertIs(self.before, self.store.state)

    def test_rejects_an_unknown_mission(self):
        result = get_history("MISSION-9", store=self.store)

        self.assertEqual(("rejected", "unknown_mission"), (result.status, result.reason))
        self.assertIs(self.before, self.store.state)

    def test_rejects_a_blank_mission_id(self):
        result = get_history("  ", store=self.store)

        self.assertEqual(("rejected", "invalid_input"), (result.status, result.reason))
        self.assertIs(self.before, self.store.state)
