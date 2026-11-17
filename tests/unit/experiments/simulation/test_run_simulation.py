"""Run isolation, determinism, and horizon semantics for scenarios."""

import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from rescue.bootstrap import new_run
from rescue.communication.models import CommunicationMessage, MessageDelivery
from rescue.demo import _baseline, _scenarios
from rescue.experiments.models import (
    RescueScenario,
    RunBaseline,
    ScriptedResponse,
)
from rescue.experiments.simulation import simulate
from rescue.market.models.availability import ShipAvailability
from rescue.market.models.b3_market import B3Market
from rescue.market.models.fleet import Ship
from rescue.market.models.offers import ShipOffer, ShipOfferRevision
from rescue.market.models.procurement import SeatRFQ
from rescue.market.models.quotes import RFQOffer
from rescue.mission.models import MissionData, SeatRequest
from rescue.mission.rules import add_request, register
from rescue.mobilisation.models import MobilisationPolicy
from rescue.values import DomainValidationError, TransitionContext


def baseline_state():
    mission = register(
        MissionData(
            mission_id="MISSION-1",
            station_name="Station One",
            people_count=2,
            created_at=0,
        )
    )
    request = SeatRequest(
        request_id="REQUEST-1",
        command_id="COMMAND-1",
        mission_id="MISSION-1",
        ship_id="SHIP-1",
        requested_seats=2,
        confirmed_seats=0,
        outcome="pending",
        submitted_at=1,
        response_deadline=20,
        revision_id="REVISION-1",
    )
    mission = add_request(
        mission,
        request,
        TransitionContext("EVENT-1", 1, "request_created"),
    )
    ship = Ship(ship_id="SHIP-1", name="Rescue One")
    availability = ShipAvailability(
        availability_id="AVAIL-1",
        ship_id="SHIP-1",
        total_seats=6,
        arrival_estimate_seconds=4,
        available=True,
        recorded_at=0,
    )
    rfq = SeatRFQ(
        rfq_id="RFQ-1",
        mission_id="MISSION-1",
        ship_id="SHIP-1",
        availability_id="AVAIL-1",
        requested_seats=2,
        status="quoted",
        sent_at=0,
        response_deadline=15,
    )
    held_quote = RFQOffer(
        offer_id="QUOTE-1",
        rfq_id="RFQ-1",
        offered_seats=1,
        arrival_estimate_seconds=4,
        expires_at=30,
        recorded_at=2,
        status="held",
    )
    message = CommunicationMessage(
        message_id="MESSAGE-1",
        correlation_id="REQUEST-1",
        request_id="REQUEST-1",
        kind="request",
        payload=(("requested_seats", 2),),
        sent_at=1,
    )
    delivery = MessageDelivery(
        delivery_id="DELIVERY-1",
        attempt_number=1,
        received_at=1,
        disposition="applied",
        reason="response_applied",
    )
    revision = ShipOfferRevision(
        revision_id="REVISION-1",
        revision_number=1,
        capacity=6,
        arrival_estimate_seconds=4,
        available=True,
        recorded_at=0,
    )
    market = B3Market(
        market_id="MARKET-1",
        ships=(ship,),
        availabilities=(availability,),
        rfqs=(rfq,),
        quotes=(held_quote,),
        offers=(
            ShipOffer(
                offer_id="OFFER-1",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                revisions=(revision,),
            ),
        ),
    )
    return RunBaseline(
        missions=(mission,),
        market=market,
        command_index=(("SOURCE-RUN", "COMMAND-1", "create_request", ("payload",), request),),
        message_index=((message, (delivery,)),),
        delivery_index=((delivery.delivery_id, message.message_id, delivery),),
        decision_index=(),
    )


def scenario_value(*, horizon=10, seed=41):
    return RescueScenario(
        scenario_id="SCENARIO-1",
        revision=1,
        name="Baseline with a pending request",
        baseline=baseline_state(),
        response_rules=(),
        availability_changes=(
            ShipAvailability(
                availability_id="AVAIL-AT-HORIZON",
                ship_id="SHIP-1",
                total_seats=4,
                arrival_estimate_seconds=5,
                available=True,
                recorded_at=horizon,
            ),
        ),
        time_horizon_seconds=horizon,
        seed=seed,
        event_budget=100,
        communication_profiles=(),
    )


def policy_value():
    return MobilisationPolicy(
        policy_id="EARLIEST",
        revision=1,
        name="Earliest arrival",
        selection_criteria="earliest_arrival",
    )


def normalized_run(snapshot):
    return (
        snapshot.run.scenario_id,
        snapshot.run.scenario_revision,
        snapshot.run.policy_id,
        snapshot.run.policy_revision,
        snapshot.run.started_at,
        snapshot.run.finished_at,
        snapshot.run.status,
        snapshot.run.result,
        tuple(
            (
                mission.mission_id,
                mission.people_count,
                tuple(
                    (
                        request.command_id,
                        request.requested_seats,
                        request.confirmed_seats,
                        request.outcome,
                        request.revision_id,
                    )
                    for request in mission.requests
                ),
                tuple(
                    (entry.action, entry.confirmed_seats_delta, entry.pending_seats_delta)
                    for entry in mission.history
                ),
            )
            for mission in snapshot.missions
        ),
        snapshot.market.quotes,
        tuple(entry[1:] for entry in snapshot.command_index),
        snapshot.message_index,
        snapshot.delivery_index,
        snapshot.decision_index,
    )


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def rng_scenario(seed):
    _, partial_refusal, _ = _scenarios(_baseline())
    return replace(
        partial_refusal,
        response_rules=(
            ScriptedResponse(ship_id="SHIP-EARLY", request_ordinal=1, outcome="partially_accepted"),
        ),
        seed=seed,
    )


def fixture_text(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


class ExperimentRunnerTests(unittest.TestCase):
    def test_each_run_copies_pending_requests_holds_history_and_identity_indexes(self):
        scenario = scenario_value()
        policy = policy_value()
        baseline_before = scenario.baseline

        first = simulate(scenario, policy, run_id="RUN-A", start_run=new_run)
        second = simulate(scenario, policy, run_id="RUN-B", start_run=new_run)

        for snapshot in (first, second):
            self.assertEqual(snapshot.missions[0].requests, scenario.baseline.missions[0].requests)
            self.assertEqual(snapshot.missions[0].history, scenario.baseline.missions[0].history)
            self.assertEqual(snapshot.market.quotes, scenario.baseline.market.quotes)
            self.assertEqual(len(snapshot.command_index), len(scenario.baseline.command_index))
            self.assertEqual(snapshot.message_index, scenario.baseline.message_index)
            self.assertEqual(snapshot.delivery_index, scenario.baseline.delivery_index)
            self.assertEqual(len(snapshot.decision_index), len(scenario.baseline.decision_index))

        self.assertEqual(scenario.baseline, baseline_before)
        self.assertEqual(scenario.baseline.market.availabilities[0].total_seats, 6)
        self.assertEqual(first.run.run_id, "RUN-A")
        self.assertEqual(second.run.run_id, "RUN-B")

    def test_same_scenario_policy_and_seed_reproduce_normalized_runs(self):
        scenario = scenario_value(seed=7)
        policy = policy_value()

        runs = tuple(
            simulate(scenario, policy, run_id=f"REPEAT-{index}", start_run=new_run)
            for index in range(3)
        )

        self.assertEqual(normalized_run(runs[0]), normalized_run(runs[1]))
        self.assertEqual(normalized_run(runs[1]), normalized_run(runs[2]))

    def test_horizon_time_availability_change_is_applied_before_incomplete_stop(self):
        scenario = scenario_value(horizon=Decimal("10"))

        snapshot = simulate(scenario, policy_value(), run_id="RUN-HORIZON", start_run=new_run)

        self.assertEqual(snapshot.run.status, "horizon_reached")
        self.assertEqual(snapshot.run.finished_at, Decimal("10"))
        self.assertEqual(snapshot.market.availabilities[-1].availability_id, "AVAIL-AT-HORIZON")
        self.assertEqual(snapshot.market.availabilities[-1].total_seats, 4)
        self.assertEqual(snapshot.missions[0].requests[0].outcome, "pending")
        self.assertEqual(snapshot.run.result.completed, False)
        self.assertIsNone(snapshot.run.result.confirmation_elapsed_seconds)

    def test_seeded_runs_match_the_main_fixture(self):
        runs = {
            "seeded_snapshot.txt": scenario_value(),
            "seeded_snapshot_seed7.txt": scenario_value(horizon=10, seed=7),
            "seeded_rng_scenario.txt": rng_scenario(41),
        }

        for name, scenario in runs.items():
            with self.subTest(name=name):
                snapshot = simulate(scenario, policy_value(), run_id="FIXTURE", start_run=new_run)
                self.assertEqual(repr(snapshot) + "\n", fixture_text(name))

    def test_rng_scenario_output_depends_on_its_seed(self):
        outputs = {
            repr(simulate(rng_scenario(seed), policy_value(), run_id="FIXTURE", start_run=new_run))
            for seed in range(1, 9)
        }

        self.assertGreater(len(outputs), 1)

    def test_start_run_is_required(self):
        with self.assertRaises(TypeError):
            simulate(scenario_value(), policy_value(), run_id="RUN-NO-START")

    def test_non_callable_start_run_is_rejected(self):
        with self.assertRaises(DomainValidationError):
            simulate(scenario_value(), policy_value(), run_id="RUN-NONE", start_run=None)


if __name__ == "__main__":
    unittest.main()
