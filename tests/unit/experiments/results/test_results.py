"""Simulation result metrics derived from immutable run snapshots."""

import unittest
from decimal import Decimal

from rescue.experiments.models import RunSnapshot, SimulationRun
from rescue.experiments.results import summarize
from rescue.market.models.b3_market import B3Market
from rescue.market.models.offers import ShipOffer, ShipOfferRevision
from rescue.mission.models import MissionData, SeatRequest
from rescue.mission.rules import add_request, apply_outcome, register
from rescue.values import TransitionContext


def mission_with_requests(mission_id, demand, request_specs):
    mission = register(
        MissionData(
            mission_id=mission_id,
            station_name=f"Station {mission_id}",
            people_count=demand,
            created_at=0,
        )
    )
    revisions = {}
    for index, spec in enumerate(request_specs, start=1):
        request_id = f"{mission_id}-request-{index}"
        ship_id = spec["ship_id"]
        revision_id = spec["revision_id"]
        submitted_at = spec["submitted_at"]
        request = SeatRequest(
            request_id=request_id,
            command_id=f"{mission_id}-command-{index}",
            mission_id=mission_id,
            ship_id=ship_id,
            requested_seats=spec["requested_seats"],
            confirmed_seats=0,
            outcome="pending",
            submitted_at=submitted_at,
            revision_id=revision_id,
        )
        mission = add_request(
            mission,
            request,
            TransitionContext(
                event_id=f"{mission_id}-created-{index}",
                at=submitted_at,
                reason="request_created",
            ),
        )
        if spec["outcome"] != "pending":
            mission = apply_outcome(
                mission,
                request_id,
                spec["outcome"],
                spec["confirmed_seats"],
                TransitionContext(
                    event_id=f"{mission_id}-closed-{index}",
                    at=spec["closed_at"],
                    reason=spec["outcome"],
                ),
            )
        revisions[revision_id] = ShipOfferRevision(
            revision_id=revision_id,
            revision_number=1,
            capacity=max(demand, spec["requested_seats"]),
            arrival_estimate_seconds=spec["arrival_estimate_seconds"],
            available=True,
            recorded_at=spec["revision_recorded_at"],
        )
    offers = tuple(
        ShipOffer(
            offer_id=f"offer-{mission_id}-{ship_id}",
            mission_id=mission_id,
            ship_id=ship_id,
            revisions=(revision,),
        )
        for (ship_id, revision_id), revision in {
            (spec["ship_id"], spec["revision_id"]): revisions[spec["revision_id"]]
            for spec in request_specs
        }.items()
    )
    return mission, offers


def run_snapshot(*, started_at, finished_at, status, missions, offers):
    run = SimulationRun(
        run_id=f"run-{status}-{started_at}",
        scenario_id="scenario-1",
        scenario_revision=1,
        policy_id="policy-1",
        policy_revision=1,
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        result=None,
    )
    return RunSnapshot(
        run=run,
        missions=tuple(missions),
        market=B3Market(market_id="market-run", offers=tuple(offers)),
    )


class SimulationResultTests(unittest.TestCase):
    def test_counts_confirmed_unmet_requests_and_pending_seats_released(self):
        mission, offers = mission_with_requests(
            "mission-1",
            5,
            (
                {
                    "ship_id": "ship-1",
                    "revision_id": "revision-1",
                    "requested_seats": 5,
                    "confirmed_seats": 0,
                    "outcome": "refused",
                    "submitted_at": 10,
                    "closed_at": 12,
                    "revision_recorded_at": 9,
                    "arrival_estimate_seconds": 4,
                },
                {
                    "ship_id": "ship-2",
                    "revision_id": "revision-2",
                    "requested_seats": 5,
                    "confirmed_seats": 0,
                    "outcome": "expired",
                    "submitted_at": 13,
                    "closed_at": 18,
                    "revision_recorded_at": 12,
                    "arrival_estimate_seconds": 3,
                },
                {
                    "ship_id": "ship-3",
                    "revision_id": "revision-3",
                    "requested_seats": 5,
                    "confirmed_seats": 2,
                    "outcome": "partially_accepted",
                    "submitted_at": 19,
                    "closed_at": 22,
                    "revision_recorded_at": 18,
                    "arrival_estimate_seconds": 6,
                },
            ),
        )
        snapshot = run_snapshot(
            started_at=10,
            finished_at=25,
            status="horizon_reached",
            missions=(mission,),
            offers=offers,
        )

        result = summarize(snapshot)

        self.assertFalse(result.completed)
        self.assertEqual(result.confirmed_seats, 2)
        self.assertEqual(result.unmet_demand, 3)
        self.assertEqual(result.requests_sent, 3)
        # Two fully released requests plus the unconfirmed portion of the partial response.
        self.assertEqual(result.released_seats, 13)
        self.assertGreater(result.released_seats, mission.people_count)
        self.assertIsNone(result.confirmation_elapsed_seconds)

    def test_latest_arrival_uses_the_common_run_start_reference(self):
        mission_a, offers_a = mission_with_requests(
            "mission-a",
            4,
            (
                {
                    "ship_id": "ship-a",
                    "revision_id": "revision-a",
                    "requested_seats": 4,
                    "confirmed_seats": 4,
                    "outcome": "accepted",
                    "submitted_at": 11,
                    "closed_at": 15,
                    "revision_recorded_at": 12,
                    "arrival_estimate_seconds": 5,
                },
            ),
        )
        mission_b, offers_b = mission_with_requests(
            "mission-b",
            6,
            (
                {
                    "ship_id": "ship-b",
                    "revision_id": "revision-b",
                    "requested_seats": 6,
                    "confirmed_seats": 6,
                    "outcome": "accepted",
                    "submitted_at": 21,
                    "closed_at": 25,
                    "revision_recorded_at": 20,
                    "arrival_estimate_seconds": 8,
                },
            ),
        )
        snapshot = run_snapshot(
            started_at=10,
            finished_at=25,
            status="completed",
            missions=(mission_a, mission_b),
            offers=(*offers_a, *offers_b),
        )

        result = summarize(snapshot)

        self.assertTrue(result.completed)
        self.assertEqual(result.confirmed_seats, 10)
        self.assertEqual(result.unmet_demand, 0)
        self.assertEqual(result.requests_sent, 2)
        self.assertEqual(result.confirmation_elapsed_seconds, Decimal("15"))
        # max(12 + 5, 20 + 8) - common run start 10 = 18 seconds.
        self.assertEqual(result.latest_arrival_estimate_seconds, Decimal("18"))

    def test_no_confirmations_produce_unknown_arrival_and_no_completion_time(self):
        mission, offers = mission_with_requests(
            "mission-1",
            3,
            (
                {
                    "ship_id": "ship-1",
                    "revision_id": "revision-1",
                    "requested_seats": 3,
                    "confirmed_seats": 0,
                    "outcome": "refused",
                    "submitted_at": 10,
                    "closed_at": 12,
                    "revision_recorded_at": 9,
                    "arrival_estimate_seconds": 4,
                },
            ),
        )
        snapshot = run_snapshot(
            started_at=10,
            finished_at=20,
            status="horizon_reached",
            missions=(mission,),
            offers=offers,
        )

        result = summarize(snapshot)

        self.assertFalse(result.completed)
        self.assertEqual(result.confirmed_seats, 0)
        self.assertEqual(result.unmet_demand, 3)
        self.assertIsNone(result.confirmation_elapsed_seconds)
        self.assertIsNone(result.latest_arrival_estimate_seconds)


if __name__ == "__main__":
    unittest.main()
