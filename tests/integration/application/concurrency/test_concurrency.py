"""Concurrency checks for shared ship inventory across application calls."""

import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from rescue.application.contracts import (
    PublishAvailability,
    RecordQuote,
    RegisterMission,
    RegisterShip,
    RequestQuotes,
)
from rescue.bootstrap import new_run
from rescue.market.models.availability import ShipAvailability
from rescue.market.models.quotes import RFQOffer


class CentralConcurrencyTests(unittest.TestCase):
    def test_only_one_of_two_concurrent_four_seat_quotes_holds_capacity_six(self):
        central = new_run("RUN-1", "CENTRAL-1").central
        for mission_id in ("MISSION-A", "MISSION-B"):
            central.register_mission(
                RegisterMission(
                    mission_id=mission_id,
                    station_name=f"Station {mission_id}",
                    people_count=8,
                    created_at=0,
                )
            )
        central.register_ship(RegisterShip(ship_id="SHIP-1", name="Rescue One"))
        central.publish_availability(
            PublishAvailability(
                availability=ShipAvailability(
                    availability_id="AVAIL-1",
                    ship_id="SHIP-1",
                    total_seats=6,
                    arrival_estimate_seconds=10,
                    available=True,
                    recorded_at=0,
                )
            )
        )

        quotes = []
        for mission_id in ("MISSION-A", "MISSION-B"):
            rfq = central.request_quotes(RequestQuotes(mission_id=mission_id, now=1)).value[0]
            quotes.append(
                RFQOffer(
                    offer_id=f"QUOTE-{mission_id}",
                    rfq_id=rfq.rfq_id,
                    offered_seats=4,
                    arrival_estimate_seconds=10,
                    expires_at=100,
                    recorded_at=2,
                    status="held",
                )
            )

        barrier = Barrier(3)

        def record(quote):
            barrier.wait(timeout=5)
            return central.record_quote(RecordQuote(offer=quote, now=2))

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(record, quote) for quote in quotes]
            barrier.wait(timeout=5)
            results = [future.result(timeout=5) for future in futures]

        self.assertEqual(sum(result.status == "applied" for result in results), 1)
        self.assertEqual(sum(result.status == "rejected" for result in results), 1)
        rejected = next(result for result in results if result.status == "rejected")
        self.assertEqual(rejected.reason, "insufficient_capacity")
        held = next(result for result in results if result.status == "applied")
        self.assertEqual(held.value.status, "held")

        for mission_id in ("MISSION-A", "MISSION-B"):
            self.assertEqual(central.get_progress(mission_id, now=3).value.pending, 0)
            self.assertEqual(central.get_history(mission_id).value, ())


if __name__ == "__main__":
    unittest.main()
