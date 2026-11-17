"""Validation of the run baseline value."""

import unittest

from rescue.experiments.models.scenario.run_baseline import RunBaseline
from rescue.market.models.b3_market import B3Market
from rescue.market.models.fleet import Ship
from rescue.mission.models import MissionData
from rescue.mission.rules import register


def mission(mission_id="MISSION-1"):
    return register(MissionData(mission_id, "Station One", 4, 0))


def market():
    return B3Market("MARKET-1", ships=(Ship("SHIP-1", "Rescue One"),))


class RunBaselineTests(unittest.TestCase):
    def test_valid_baseline_keeps_missions_and_market(self):
        baseline = RunBaseline(missions=[mission()], market=market())
        self.assertEqual(baseline.missions, (mission(),))
        self.assertEqual(baseline.command_index, ())

    def test_non_mission_and_duplicate_missions_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be Mission values"):
            RunBaseline(missions=("x",), market=market())
        with self.assertRaisesRegex(ValueError, "must be unique"):
            RunBaseline(missions=(mission(), mission()), market=market())

    def test_market_must_be_b3_market(self):
        with self.assertRaisesRegex(ValueError, "B3Market"):
            RunBaseline(missions=(mission(),), market="market")

    def test_indexes_must_be_immutable(self):
        with self.assertRaisesRegex(ValueError, "immutable"):
            RunBaseline(missions=(mission(),), market=market(), command_index=([],))

    def test_market_parts_must_be_deeply_immutable(self):
        mutable_market = B3Market("MARKET-1", ships=([],))
        with self.assertRaisesRegex(ValueError, "deeply immutable"):
            RunBaseline(missions=(mission(),), market=mutable_market)


if __name__ == "__main__":
    unittest.main()
