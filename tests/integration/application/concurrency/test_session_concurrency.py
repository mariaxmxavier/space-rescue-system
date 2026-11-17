import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from rescue.application.contracts import (
    CreateRequest,
    PublishAvailability,
    PublishOffer,
    RecordResponse,
    RegisterMission,
    RegisterShip,
)
from rescue.bootstrap import new_run
from rescue.communication.models import FlowDirection, SessionEnvelope
from rescue.market.models.availability import ShipAvailability
from rescue.market.models.offers import ShipOfferRevision

SESSIONS = ("SESSION-A", "SESSION-B", "SESSION-C")
PER_SESSION = 2
DEMAND = len(SESSIONS) * PER_SESSION


def _setup():
    central = new_run("RUN-SESSIONS", "CENTRAL-SESSIONS").central
    central.register_mission(RegisterMission("MISSION-1", "Station", DEMAND, 0))
    central.register_ship(RegisterShip("SHIP-1", "Rescue One"))
    central.publish_availability(
        PublishAvailability(ShipAvailability("AVAIL-1", "SHIP-1", 20, 5, True, 0))
    )
    central.publish_offer(
        PublishOffer(
            "OFFER-1", "MISSION-1", "SHIP-1", ShipOfferRevision("REV-1", 1, 20, 5, True, 0)
        )
    )
    requests = {}
    for session in SESSIONS:
        requests[session] = [
            central.create_request(
                CreateRequest(
                    command_id=f"COMMAND-{session}-{index}",
                    mission_id="MISSION-1",
                    ship_id="SHIP-1",
                    requested_seats=1,
                    revision_id="REV-1",
                    now=0,
                    response_deadline=None,
                )
            ).value.request_id
            for index in range(1, PER_SESSION + 1)
        ]
    return central, requests


def _confirm(central, session, request_id, sequence, *, delivery_suffix="1"):
    return central.record_response(
        RecordResponse(
            message_id=f"MSG-{session}-{sequence}",
            delivery_id=f"DEL-{session}-{sequence}-{delivery_suffix}",
            attempt_number=1,
            request_id=request_id,
            outcome="accepted",
            confirmed_seats=1,
            sent_at=1,
            received_at=2,
            envelope=SessionEnvelope(session, 1, FlowDirection.INBOUND, sequence),
        )
    )


class SessionConcurrencyTests(unittest.TestCase):
    def test_concurrent_sessions_share_seats_without_cross_session_effects(self):
        """Threads from several sessions confirm shared seats and keep totals and counters exact."""
        central, requests = _setup()
        barrier = Barrier(len(SESSIONS))
        samples = []

        def run_session(session):
            barrier.wait(timeout=5)
            results = []
            for sequence, request_id in enumerate(requests[session], start=1):
                results.append(_confirm(central, session, request_id, sequence))
                progress = central.get_progress("MISSION-1", 100).value
                samples.append(progress.confirmed + progress.pending)
            return results

        with ThreadPoolExecutor(max_workers=len(SESSIONS)) as executor:
            futures = [executor.submit(run_session, session) for session in SESSIONS]
            results = [future.result(timeout=10) for future in futures]

        for session_results in results:
            self.assertEqual([item.status for item in session_results], ["applied"] * PER_SESSION)
        self.assertTrue(all(total <= DEMAND for total in samples))
        progress = central.get_progress("MISSION-1", 100).value
        self.assertEqual((progress.confirmed, progress.pending), (DEMAND, 0))
        for session in SESSIONS:
            stored = central.get_session(session).value
            self.assertEqual(stored.next_inbound, PER_SESSION + 1)
            self.assertEqual(stored.next_outbound, PER_SESSION + 1)
            self.assertEqual(len(stored.reports), PER_SESSION)

    def test_concurrent_duplicate_sequences_are_not_counted_twice(self):
        """Racing duplicate confirmations on every session add no seats and no counters."""
        central, requests = _setup()
        barrier = Barrier(len(SESSIONS) * 2)

        def run(session, suffix):
            barrier.wait(timeout=5)
            return [
                _confirm(central, session, request_id, sequence, delivery_suffix=suffix)
                for sequence, request_id in enumerate(requests[session], start=1)
            ]

        with ThreadPoolExecutor(max_workers=len(SESSIONS) * 2) as executor:
            futures = [
                executor.submit(run, session, suffix) for session in SESSIONS for suffix in "12"
            ]
            results = [future.result(timeout=10) for future in futures]

        applied = sum(item.status == "applied" for batch in results for item in batch)
        self.assertEqual(applied, DEMAND)
        progress = central.get_progress("MISSION-1", 100).value
        self.assertEqual((progress.confirmed, progress.pending), (DEMAND, 0))
        for session in SESSIONS:
            stored = central.get_session(session).value
            self.assertEqual(stored.next_inbound, PER_SESSION + 1)
            self.assertEqual(len(stored.reports), PER_SESSION)


if __name__ == "__main__":
    unittest.main()
