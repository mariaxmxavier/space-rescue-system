"""Validation of the rescue scenario value."""

import unittest
from decimal import Decimal

from rescue.experiments.models import (
    CommunicationProfile,
    RunBaseline,
    ScriptedResponse,
)
from rescue.experiments.models.scenario.rescue_scenario import RescueScenario
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

    def test_name_and_baseline_are_required(self):
        with self.assertRaisesRegex(ValueError, "name must be nonblank"):
            scenario(name=" ")
        with self.assertRaisesRegex(ValueError, "requires a RunBaseline"):
            scenario(baseline="baseline")

    def test_collections_must_hold_typed_values(self):
        with self.assertRaisesRegex(ValueError, "must contain ScriptedResponse"):
            scenario(response_rules=("rule",))
        with self.assertRaisesRegex(ValueError, "must be ShipAvailability"):
            scenario(availability_changes=("change",))
        with self.assertRaisesRegex(ValueError, "must contain CommunicationProfile"):
            scenario(communication_profiles=("profile",))

    def test_duplicate_response_rules_are_rejected(self):
        rule = ScriptedResponse("SHIP-1", 1, "refused")
        with self.assertRaisesRegex(ValueError, "only one response rule"):
            scenario(response_rules=(rule, rule))

    def test_duplicate_profile_ids_or_ships_are_rejected(self):
        first = CommunicationProfile("PROFILE-1", "SHIP-1", 0, 0, 0)
        same_id = CommunicationProfile("PROFILE-1", "SHIP-1", 0, 0, 0)
        with self.assertRaisesRegex(ValueError, "unique IDs and ships"):
            scenario(communication_profiles=(first, same_id))

    def test_duplicate_availability_times_are_rejected(self):
        first = ShipAvailability("CHANGE-1", "SHIP-1", 0, 0, True, 1)
        second = ShipAvailability("CHANGE-2", "SHIP-1", 0, 0, True, 1)
        with self.assertRaisesRegex(ValueError, "duplicate scenario availability"):
            scenario(availability_changes=(first, second))

    def test_valid_collections_are_kept_as_tuples(self):
        value = scenario(
            response_rules=[ScriptedResponse("SHIP-1", 1, "refused")],
            availability_changes=[ShipAvailability("CHANGE-1", "SHIP-1", 0, 0, True, 1)],
            communication_profiles=[CommunicationProfile("PROFILE-1", "SHIP-1", 0, 0, 0)],
        )
        self.assertIsInstance(value.response_rules, tuple)
        self.assertIsInstance(value.availability_changes, tuple)
        self.assertIsInstance(value.communication_profiles, tuple)


if __name__ == "__main__":
    unittest.main()
