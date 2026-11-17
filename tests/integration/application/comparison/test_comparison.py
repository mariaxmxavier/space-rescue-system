"""Comparison runs use immutable scenario inputs and leave operations intact."""

import unittest

from rescue.application.contracts import ComparePolicies, RegisterMission
from rescue.bootstrap import new_run
from rescue.experiments.models import (
    RescueScenario,
    RunBaseline,
    ScriptedResponse,
)
from rescue.market.models.availability import ShipAvailability
from rescue.market.models.b3_market import B3Market
from rescue.market.models.fleet import Ship
from rescue.market.models.offers import ShipOffer, ShipOfferRevision
from rescue.mission.models import MissionData
from rescue.mission.rules import register
from rescue.mobilisation.models import MobilisationPolicy
from rescue.values import DomainValidationError


def policy(policy_id, strategy):
    return MobilisationPolicy(
        policy_id=policy_id,
        revision=1,
        name=policy_id,
        selection_criteria=strategy,
    )


def scenario_value():
    mission = register(MissionData("MISSION", "Station", 4, 0))
    ships = (Ship("EARLY", "Early ship"), Ship("LARGE", "Large ship"))
    availability = (
        ShipAvailability("AV-EARLY", "EARLY", 4, 2, True, 0),
        ShipAvailability("AV-LARGE", "LARGE", 6, 5, True, 0),
    )
    offers = (
        ShipOffer(
            "OFFER-EARLY",
            "MISSION",
            "EARLY",
            (ShipOfferRevision("REV-EARLY", 1, 4, 2, True, 0),),
        ),
        ShipOffer(
            "OFFER-LARGE",
            "MISSION",
            "LARGE",
            (ShipOfferRevision("REV-LARGE", 1, 6, 5, True, 0),),
        ),
    )
    baseline = RunBaseline(
        missions=(mission,),
        market=B3Market(
            market_id="BASELINE-MARKET",
            ships=ships,
            availabilities=availability,
            offers=offers,
        ),
    )
    return RescueScenario(
        scenario_id="SCENARIO",
        revision=1,
        name="Ordinary, partial, and refusal responses",
        baseline=baseline,
        response_rules=(
            ScriptedResponse("EARLY", 1, "partially_accepted", 2),
            ScriptedResponse("EARLY", 2, "accepted"),
            ScriptedResponse("LARGE", 1, "refused"),
        ),
        availability_changes=(),
        time_horizon_seconds=8,
        seed=19,
        event_budget=100,
    )


class ComparePoliciesTests(unittest.TestCase):
    def test_two_policies_run_against_one_scenario_without_mutating_operations(self):
        earliest = policy("EARLIEST", "earliest_arrival")
        largest = policy("LARGEST", "largest_capacity")
        scenario = scenario_value()
        context = new_run(
            "OPERATIONAL",
            "CENTRAL",
            policies=(earliest, largest),
            scenarios=(scenario,),
        )
        registered = context.central.register_mission(
            RegisterMission("OP-MISSION", "Operational station", 3, 0)
        )
        self.assertEqual(registered.status, "applied")
        before = context.store.snapshot()

        result = context.central.compare(
            ComparePolicies(
                scenario_id=scenario.scenario_id,
                scenario_revision=scenario.revision,
                policy_keys=(
                    (earliest.policy_id, earliest.revision),
                    (largest.policy_id, largest.revision),
                ),
            )
        )

        self.assertEqual(result.status, "applied")
        snapshots = result.value
        self.assertEqual(len(snapshots), 2)
        self.assertEqual(
            tuple(snapshot.run.policy_id for snapshot in snapshots),
            (earliest.policy_id, largest.policy_id),
        )
        self.assertTrue(snapshots[0].run.result.completed)
        self.assertEqual(
            tuple(request.outcome for request in snapshots[0].missions[0].requests),
            ("partially_accepted", "accepted"),
        )
        self.assertEqual(
            snapshots[1].missions[0].requests[0].outcome,
            "refused",
        )
        self.assertEqual(context.store.snapshot(), before)

    def test_new_run_requires_typed_policy_and_scenario_registry_values(self):
        with self.assertRaises(DomainValidationError):
            new_run("RUN", "CENTRAL", policies=(object(),))
        with self.assertRaises(DomainValidationError):
            new_run("RUN", "CENTRAL", scenarios=(object(),))

    def test_unknown_scenario_or_policy_is_rejected_without_mutating_operations(self):
        scenario = scenario_value()
        context = new_run("RUN", "CENTRAL", scenarios=(scenario,))
        before = context.store.snapshot()

        result = context.central.compare(ComparePolicies("UNKNOWN", 1, (("UNKNOWN-POLICY", 1),)))

        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.reason, "invalid_input")
        self.assertEqual(context.store.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
