"""Scenario behavior under loss, changing availability, and repeat execution."""

import unittest

from rescue.application.contracts import (
    CreateRequest,
    PublishAvailability,
    PublishOffer,
    RegisterMission,
    RegisterShip,
)
from rescue.bootstrap import new_run
from rescue.experiments.models import (
    CommunicationProfile,
    RescueScenario,
    RunBaseline,
    ScriptedResponse,
)
from rescue.experiments.runner import simulate
from rescue.market.models.availability import ShipAvailability
from rescue.market.models.offers import ShipOfferRevision
from rescue.mobilisation.models import MobilisationPolicy


def _operational_baseline(*, demand=2, requested=2, deadline=20):
    context = new_run("RUN-OPERATIONAL", "CENTRAL-OPERATIONAL")
    central = context.central
    central.register_mission(RegisterMission("MISSION-1", "Station One", demand, 0))
    central.register_ship(RegisterShip("SHIP-1", "Rescue One"))
    central.publish_availability(
        PublishAvailability(ShipAvailability("AVAIL-1", "SHIP-1", 4, 3, True, 0))
    )
    central.publish_offer(
        PublishOffer(
            offer_id="OFFER-1",
            mission_id="MISSION-1",
            ship_id="SHIP-1",
            revision=ShipOfferRevision("REVISION-1", 1, 4, 3, True, 0),
        )
    )
    if requested:
        central.create_request(
            CreateRequest(
                command_id="COMMAND-BASELINE",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                requested_seats=requested,
                revision_id="REVISION-1",
                now=0,
                response_deadline=deadline,
            )
        )
    state = context.store.snapshot()
    baseline = RunBaseline(
        missions=state.missions,
        market=state.market,
        command_index=state.command_index,
        message_index=state.message_index,
        delivery_index=state.delivery_index,
        decision_index=state.decision_index,
    )
    return context, baseline


def _scenario(
    baseline,
    *,
    horizon=10,
    responses=(),
    profile=None,
    availability_changes=(),
    seed=21,
    event_budget=100,
):
    return RescueScenario(
        scenario_id="SCENARIO-1",
        revision=1,
        name="Resilience scenario",
        baseline=baseline,
        response_rules=tuple(responses),
        availability_changes=tuple(availability_changes),
        time_horizon_seconds=horizon,
        seed=seed,
        event_budget=event_budget,
        communication_profiles=() if profile is None else (profile,),
    )


def _policy():
    return MobilisationPolicy(
        policy_id="EARLIEST",
        revision=1,
        name="Earliest arrival",
        selection_criteria="earliest_arrival",
    )


def _profile(*, outbound=0, decision=0, returning=0, loss=(), duplicate=()):
    return CommunicationProfile(
        profile_id="PROFILE-1",
        ship_id="SHIP-1",
        outbound_delay_seconds=outbound,
        decision_delay_seconds=decision,
        return_delay_seconds=returning,
        loss_rule=tuple(loss),
        duplication_rule=tuple(duplicate),
    )


class ResilienceSimulationTests(unittest.TestCase):
    def test_refusal_releases_capacity_and_remobilises_until_confirmed(self):
        _, baseline = _operational_baseline()
        scenario = _scenario(
            baseline,
            responses=(
                ScriptedResponse("SHIP-1", 1, "refused"),
                ScriptedResponse("SHIP-1", 2, "accepted", confirmed_seats=2),
            ),
        )

        snapshot = simulate(scenario, _policy(), run_id="RUN-REMOBILISE")

        self.assertEqual(snapshot.run.status, "completed")
        self.assertEqual(snapshot.run.result.confirmed_seats, 2)
        self.assertEqual(snapshot.run.result.unmet_demand, 0)
        self.assertEqual(
            tuple(request.outcome for request in snapshot.missions[0].requests),
            ("refused", "accepted"),
        )
        self.assertEqual(snapshot.run.result.requests_sent, 2)
        self.assertEqual(snapshot.run.result.released_seats, 2)

    def test_lost_response_and_capacity_change_leave_pending_request_at_horizon(self):
        context, baseline = _operational_baseline()
        before = context.store.snapshot()
        availability = ShipAvailability(
            availability_id="AVAIL-CHANGED",
            ship_id="SHIP-1",
            total_seats=3,
            arrival_estimate_seconds=6,
            available=True,
            recorded_at=2,
        )
        scenario = _scenario(
            baseline,
            horizon=5,
            responses=(ScriptedResponse("SHIP-1", 1, "accepted", confirmed_seats=2),),
            profile=_profile(outbound=1, decision=2, returning=1, loss=(1,)),
            availability_changes=(availability,),
        )

        snapshot = simulate(scenario, _policy(), run_id="RUN-LOSS-CAPACITY")

        self.assertEqual(snapshot.run.status, "horizon_reached")
        self.assertFalse(snapshot.run.result.completed)
        self.assertIsNone(snapshot.run.result.confirmation_elapsed_seconds)
        self.assertEqual(snapshot.missions[0].requests[0].outcome, "pending")
        self.assertEqual(snapshot.missions[0].requests[0].confirmed_seats, 0)
        self.assertEqual(snapshot.market.availabilities[-1], availability)
        self.assertEqual(snapshot.message_index[0][1][0].disposition, "lost")
        self.assertIsNone(snapshot.message_index[0][1][0].received_at)
        after = context.store.snapshot()
        self.assertEqual(after.missions, before.missions)
        self.assertEqual(after.market, before.market)
        self.assertEqual(scenario.baseline, baseline)

    def test_same_seed_three_runs_match_and_zero_delay_duplicates_are_bounded(self):
        _, baseline = _operational_baseline()
        scenario = _scenario(
            baseline,
            horizon=10,
            responses=(ScriptedResponse("SHIP-1", 1, "refused"),),
            profile=_profile(duplicate=(1,)),
            seed=87,
            event_budget=12,
        )

        snapshots = tuple(
            simulate(scenario, _policy(), run_id=f"RUN-REPEAT-{index}") for index in range(3)
        )
        normalized = tuple(
            (
                snapshot.run.status,
                snapshot.run.finished_at,
                snapshot.run.result,
                tuple(
                    (request.requested_seats, request.confirmed_seats, request.outcome)
                    for request in snapshot.missions[0].requests
                ),
                tuple(
                    (entry.action, entry.confirmed_seats_delta, entry.pending_seats_delta)
                    for entry in snapshot.missions[0].history
                ),
                snapshot.market.availabilities,
                tuple(
                    (
                        message.request_id,
                        message.kind,
                        message.payload,
                        message.sent_at,
                        tuple(
                            (delivery.attempt_number, delivery.received_at, delivery.disposition)
                            for delivery in deliveries
                        ),
                    )
                    for message, deliveries in snapshot.message_index
                ),
            )
            for snapshot in snapshots
        )

        self.assertEqual(normalized[0], normalized[1])
        self.assertEqual(normalized[1], normalized[2])
        self.assertEqual(len(snapshots[0].message_index[0][1]), 2)
        self.assertEqual(
            {delivery.attempt_number for delivery in snapshots[0].message_index[0][1]},
            {1, 2},
        )
        self.assertEqual(
            len({delivery.delivery_id for delivery in snapshots[0].message_index[0][1]}),
            2,
        )


if __name__ == "__main__":
    unittest.main()
