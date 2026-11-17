"""Concurrency checks for per-mission decision order numbers."""

import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from rescue.application.contracts import (
    CancelRequest,
    CreateRequest,
    PublishAvailability,
    PublishOffer,
    RegisterMission,
    RegisterShip,
)
from rescue.bootstrap import new_run
from rescue.market.models.availability import ShipAvailability
from rescue.market.models.offers import ShipOfferRevision

MISSIONS = ("MISSION-A", "MISSION-B")
THREADS_PER_MISSION = 8


def build_central():
    central = new_run("RUN-1", "CENTRAL-1").central
    central.register_ship(RegisterShip(ship_id="SHIP-1", name="Rescue One"))
    central.publish_availability(
        PublishAvailability(
            availability=ShipAvailability(
                availability_id="AVAIL-1",
                ship_id="SHIP-1",
                total_seats=100,
                arrival_estimate_seconds=10,
                available=True,
                recorded_at=0,
            )
        )
    )
    for mission_id in MISSIONS:
        central.register_mission(
            RegisterMission(
                mission_id=mission_id,
                station_name=f"Station {mission_id}",
                people_count=THREADS_PER_MISSION,
                created_at=0,
            )
        )
        central.publish_offer(
            PublishOffer(
                offer_id=f"OFFER-{mission_id}",
                mission_id=mission_id,
                ship_id="SHIP-1",
                revision=ShipOfferRevision(
                    revision_id=f"REV-{mission_id}",
                    revision_number=1,
                    capacity=THREADS_PER_MISSION,
                    arrival_estimate_seconds=10,
                    available=True,
                    recorded_at=0,
                ),
            )
        )
    return central


def run_together(jobs):
    barrier = Barrier(len(jobs))

    def start(job):
        barrier.wait(timeout=5)
        return job()

    with ThreadPoolExecutor(max_workers=len(jobs)) as executor:
        futures = [executor.submit(start, job) for job in jobs]
        return [future.result(timeout=10) for future in futures]


def create_job(central, mission_id, index):
    return lambda: central.create_request(
        CreateRequest(
            command_id=f"CMD-{mission_id}-{index}",
            mission_id=mission_id,
            ship_id="SHIP-1",
            requested_seats=1,
            revision_id=f"REV-{mission_id}",
            now=1,
        )
    )


def sequences(central, mission_id):
    return [entry.mission_sequence for entry in central.get_history(mission_id).value]


class MissionOrderConcurrencyTests(unittest.TestCase):
    def test_threads_on_one_mission_get_gapless_numbers_matching_history_order(self):
        """Concurrent requests on one mission get numbers 1..N in committed history order."""
        central = build_central()
        mission_id = MISSIONS[0]

        results = run_together(
            [create_job(central, mission_id, index) for index in range(THREADS_PER_MISSION)]
        )

        self.assertEqual([result.status for result in results], ["applied"] * THREADS_PER_MISSION)
        history = central.get_history(mission_id).value
        self.assertEqual(
            [entry.mission_sequence for entry in history],
            list(range(1, THREADS_PER_MISSION + 1)),
        )
        self.assertEqual(
            len({entry.event_id for entry in history}),
            THREADS_PER_MISSION,
        )

    def test_threads_on_two_missions_number_each_history_independently(self):
        """Concurrent requests on two missions number each history 1..N without crossing."""
        central = build_central()

        results = run_together(
            [
                create_job(central, mission_id, index)
                for index in range(THREADS_PER_MISSION)
                for mission_id in MISSIONS
            ]
        )

        self.assertEqual(
            [result.status for result in results], ["applied"] * (2 * THREADS_PER_MISSION)
        )
        for mission_id in MISSIONS:
            self.assertEqual(
                sequences(central, mission_id), list(range(1, THREADS_PER_MISSION + 1))
            )

    def test_mixed_creates_and_cancels_keep_each_mission_gapless(self):
        """Concurrent cancels on two missions extend each history to 2N without gaps."""
        central = build_central()
        requests = run_together(
            [
                create_job(central, mission_id, index)
                for index in range(THREADS_PER_MISSION)
                for mission_id in MISSIONS
            ]
        )

        cancels = run_together(
            [
                (
                    lambda request=result.value: central.cancel_request(
                        CancelRequest(
                            mission_id=request.mission_id,
                            request_id=request.request_id,
                            now=2,
                            reason="operator_cancelled",
                        )
                    )
                )
                for result in requests
            ]
        )

        self.assertEqual([result.status for result in cancels], ["applied"] * len(cancels))
        for mission_id in MISSIONS:
            self.assertEqual(
                sequences(central, mission_id), list(range(1, 2 * THREADS_PER_MISSION + 1))
            )


if __name__ == "__main__":
    unittest.main()
