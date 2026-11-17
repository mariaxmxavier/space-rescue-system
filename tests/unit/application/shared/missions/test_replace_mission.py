"""replace_mission tests."""

import unittest

from rescue.application.shared.replace_mission import replace_mission
from rescue.market.models.b3_market import B3Market
from rescue.mission.models import Mission
from rescue.state import RunState
from rescue.values import DomainValidationError


class ReplaceMissionTests(unittest.TestCase):
    """replace_mission swaps a registered mission by id and refuses an unregistered one.

    What: returns a new state with the mission replaced.
    When called: by tests of the shared writer.
    Why: a mutating service must never add a mission through the update path.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def setUp(self):
        self.state = RunState(
            "RUN-1",
            "CENTRAL-1",
            B3Market("MARKET-1"),
            missions=(Mission("MISSION-1", "Station One", 6, 0),),
        )

    def test_replaces_the_mission_with_the_same_id(self):
        updated = Mission("MISSION-1", "Station Two", 6, 0)
        self.assertEqual(replace_mission(self.state, updated).missions, (updated,))

    def test_refuses_an_unregistered_mission(self):
        with self.assertRaises(DomainValidationError):
            replace_mission(self.state, Mission("MISSION-9", "Station", 6, 0))
