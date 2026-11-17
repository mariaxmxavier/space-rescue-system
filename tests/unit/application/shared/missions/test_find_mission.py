"""find_mission tests."""

import unittest

from rescue.application.shared.find_mission import find_mission
from rescue.market.models.b3_market import B3Market
from rescue.mission.models import Mission
from rescue.state import RunState


class FindMissionTests(unittest.TestCase):
    """find_mission returns the stored mission for an id, by id.

    What: looks a mission up by id.
    When called: by tests of the shared lookup.
    Why: services rely on None, not an error, for a mission the run does not hold.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def setUp(self):
        self.mission = Mission("MISSION-1", "Station One", 6, 0)
        self.state = RunState("RUN-1", "CENTRAL-1", B3Market("MARKET-1"), missions=(self.mission,))

    def test_returns_the_stored_mission(self):
        self.assertIs(find_mission(self.state, "MISSION-1"), self.mission)

    def test_returns_none_for_an_unknown_mission(self):
        self.assertIsNone(find_mission(self.state, "MISSION-2"))
