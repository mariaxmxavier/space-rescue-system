"""Validation of immutable experiment and comparison inputs."""

import unittest
from decimal import Decimal

from rescue.experiments.models import (
    CommunicationProfile,
    RescueScenario,
    RunBaseline,
    ScriptedResponse,
)
from rescue.market.models.availability import ShipAvailability
from rescue.market.models.b3_market import B3Market
from rescue.market.models.fleet import Ship
from rescue.mission.models import MissionData
from rescue.mission.rules import register


def baseline():
    mission = register(MissionData("MISSION-1", "Station One", 4, 0))
    market = B3Market(
        "MARKET-1",
        ships=(Ship("SHIP-1", "Rescue One"),),
    )
    return RunBaseline(missions=(mission,), market=market)


def scenario(**changes):
    values = {
        "scenario_id": "SCENARIO-1",
        "revision": 1,
        "name": "Validation scenario",
        "baseline": baseline(),
        "response_rules": (),
        "availability_changes": (),
        "time_horizon_seconds": 20,
        "seed": 3,
        "event_budget": 100,
        "communication_profiles": (),
    }
    values.update(changes)
    return RescueScenario(**values)


class RescueScenarioTests(unittest.TestCase):
    def test_horizon_seed_and_event_budget_are_bounded(self):
        for horizon in (0, -1, Decimal("NaN"), Decimal("Infinity")):
            with self.subTest(horizon=horizon), self.assertRaises(ValueError):
                scenario(time_horizon_seconds=horizon)
        for seed in (-1, True, 1.5):
            with self.subTest(seed=seed), self.assertRaises(ValueError):
                scenario(seed=seed)
        for event_budget in (0, -1, True, 1.5):
            with self.subTest(event_budget=event_budget), self.assertRaises(ValueError):
                scenario(event_budget=event_budget)

    def test_unknown_ship_references_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown baseline ship"):
            scenario(response_rules=(ScriptedResponse("MISSING", 1, "refused"),))
        with self.assertRaisesRegex(ValueError, "unknown baseline ship"):
            scenario(availability_changes=(ShipAvailability("CHANGE-1", "MISSING", 0, 0, True, 1),))
        with self.assertRaisesRegex(ValueError, "unknown baseline ship"):
            scenario(
                communication_profiles=(CommunicationProfile("PROFILE-1", "MISSING", 0, 0, 0),)
            )

    def test_negative_communication_delay_and_unbounded_profile_rule_are_rejected(self):
        with self.assertRaises(ValueError):
            CommunicationProfile("PROFILE-1", "SHIP-1", -1, 0, 0)
        with self.assertRaises(ValueError):
            CommunicationProfile(
                "PROFILE-1",
                "SHIP-1",
                0,
                0,
                0,
                loss_rule=(1, 1),
            )
        with self.assertRaisesRegex(ValueError, "cannot also be duplicated"):
            CommunicationProfile(
                "PROFILE-1", "SHIP-1", 0, 0, 0, loss_rule=(1,), duplication_rule=(1,)
            )
        with self.assertRaisesRegex(ValueError, "cannot also be duplicated"):
            CommunicationProfile(
                "PROFILE-1", "SHIP-1", 0, 0, 0, loss_rule=(1,), reordering_rule=(1,)
            )
        for rule in ((True,), (Decimal("1"),), (0,), (-1,)):
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                CommunicationProfile("PROFILE-1", "SHIP-1", 0, 0, 0, reordering_rule=rule)


if __name__ == "__main__":
    unittest.main()
