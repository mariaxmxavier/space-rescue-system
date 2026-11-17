"""Tests of the register_mission service.

What: proves a valid command registers a mission and every refusal leaves the run state untouched.
When called: by pytest with the application unit tests.
Why: registration is the first step of every rescue, so each of its outcomes is pinned.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

import unittest

from rescue.application.contracts import RegisterMission
from rescue.application.services.missions.register_mission import register_mission
from tests.unit.application.services.fakes import FakeStore, empty_state


def command(mission_id="MISSION-1", people_count=5, created_at=0):
    return RegisterMission(
        mission_id=mission_id,
        station_name="Station A",
        people_count=people_count,
        created_at=created_at,
    )


class RegisterMissionTests(unittest.TestCase):
    def setUp(self):
        self.store = FakeStore(empty_state())

    def test_applies_and_publishes_the_new_mission(self):
        result = register_mission(command(), store=self.store)

        self.assertEqual("applied", result.status)
        self.assertEqual("MISSION-1", result.value.mission_id)
        self.assertEqual((result.value,), self.store.state.missions)

    def test_rejects_a_repeated_mission_id_as_identity_conflict(self):
        register_mission(command(), store=self.store)
        before = self.store.state

        result = register_mission(command(), store=self.store)

        self.assertEqual(("rejected", "identity_conflict"), (result.status, result.reason))
        self.assertIs(before, self.store.state)

    def test_rejects_invalid_input_and_publishes_nothing(self):
        before = self.store.state

        result = register_mission(command(people_count=0), store=self.store)

        self.assertEqual(("rejected", "invalid_input"), (result.status, result.reason))
        self.assertIs(before, self.store.state)

    def test_rejects_a_malformed_command_field_and_publishes_nothing(self):
        before = self.store.state

        result = register_mission(command(created_at=-1), store=self.store)

        self.assertEqual("rejected", result.status)
        self.assertIs(before, self.store.state)
