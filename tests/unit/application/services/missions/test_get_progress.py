"""Tests of the get_progress service.

What: proves progress is read for a known mission and refused for an unknown or malformed query.
When called: by pytest with the application unit tests.
Why: a read must never change the run state, whatever its outcome.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

import unittest

from rescue.application.contracts import RegisterMission
from rescue.application.services.missions.get_progress import get_progress
from rescue.application.services.missions.register_mission import register_mission
from tests.unit.application.services.fakes import FakeStore, empty_state


class GetProgressTests(unittest.TestCase):
    def setUp(self):
        self.store = FakeStore(empty_state())
        register_mission(
            RegisterMission(
                mission_id="MISSION-1", station_name="Station A", people_count=5, created_at=0
            ),
            store=self.store,
        )
        self.before = self.store.state

    def test_applies_with_the_mission_progress(self):
        result = get_progress("MISSION-1", 0, store=self.store)

        self.assertEqual("applied", result.status)
        self.assertEqual(5, result.value.demand)
        self.assertIs(self.before, self.store.state)

    def test_rejects_an_unknown_mission(self):
        result = get_progress("MISSION-9", 0, store=self.store)

        self.assertEqual(("rejected", "unknown_mission"), (result.status, result.reason))
        self.assertIs(self.before, self.store.state)

    def test_rejects_an_invalid_instant(self):
        result = get_progress("MISSION-1", -1, store=self.store)

        self.assertEqual(("rejected", "invalid_input"), (result.status, result.reason))
        self.assertIs(self.before, self.store.state)

    def test_rejects_a_mission_id_of_the_wrong_type(self):
        result = get_progress(None, 0, store=self.store)

        self.assertEqual("rejected", result.status)
        self.assertIs(self.before, self.store.state)
