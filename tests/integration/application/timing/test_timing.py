"""Request timing projections and deadline ordering behavior."""

import unittest
from decimal import Decimal

from rescue.application.contracts import (
    CancelRequest,
    CreateRequest,
    PublishAvailability,
    PublishOffer,
    RecordResponse,
    RegisterMission,
    RegisterShip,
)
from rescue.bootstrap import new_run
from rescue.market.models import ShipAvailability, ShipOfferRevision
from rescue.mission.rules import timing


def registered_central(*, demand=6, capacity=6):
    central = new_run("RUN-TIMING", "CENTRAL-TIMING").central
    central.register_mission(
        RegisterMission(
            mission_id="MISSION-1",
            station_name="Station One",
            people_count=demand,
            created_at=0,
        )
    )
    central.register_ship(RegisterShip(ship_id="SHIP-1", name="Rescue One"))
    central.publish_availability(
        PublishAvailability(
            availability=ShipAvailability(
                availability_id="AVAIL-1",
                ship_id="SHIP-1",
                total_seats=capacity,
                arrival_estimate_seconds=10,
                available=True,
                recorded_at=0,
            )
        )
    )
    central.publish_offer(
        PublishOffer(
            offer_id="OFFER-1",
            mission_id="MISSION-1",
            ship_id="SHIP-1",
            revision=ShipOfferRevision(
                revision_id="REV-1",
                revision_number=1,
                capacity=capacity,
                arrival_estimate_seconds=10,
                available=True,
                recorded_at=0,
            ),
        )
    )
    return central


def create_request(central, *, command_id="COMMAND-1", submitted_at=10, deadline=None, seats=3):
    return central.create_request(
        CreateRequest(
            command_id=command_id,
            mission_id="MISSION-1",
            ship_id="SHIP-1",
            requested_seats=seats,
            revision_id="REV-1",
            now=submitted_at,
            response_deadline=deadline,
        )
    )


def respond(
    central,
    request_id,
    *,
    message_id="MESSAGE-1",
    delivery_id="DELIVERY-1",
    sent_at=16,
    received_at=17,
):
    return central.record_response(
        RecordResponse(
            message_id=message_id,
            delivery_id=delivery_id,
            attempt_number=1,
            request_id=request_id,
            outcome="accepted",
            confirmed_seats=3,
            sent_at=sent_at,
            received_at=received_at,
        )
    )


class RequestTimingTests(unittest.TestCase):
    def test_receipt_17_after_submission_10_reports_seven_seconds(self):
        central = registered_central()
        created = create_request(central)
        self.assertEqual(created.status, "applied")
        response = respond(central, created.value.request_id)
        self.assertEqual(response.status, "applied")

        projection = timing(response.value, now=20)

        self.assertEqual(projection.response_elapsed_seconds, Decimal("7"))
        self.assertEqual(projection.submitted_at, Decimal("10"))
        self.assertEqual(projection.response_received_at, Decimal("17"))

    def test_optional_deadline_and_unanswered_waiting_are_preserved(self):
        central = registered_central()
        created = create_request(central)
        self.assertIsNone(created.value.response_deadline)

        projection = timing(created.value, now=13)

        self.assertIsNone(projection.response_elapsed_seconds)
        self.assertEqual(projection.waiting_seconds, Decimal("3"))
        self.assertIsNone(created.value.response_received_at)

    def test_deadline_must_follow_submission(self):
        central = registered_central()
        for deadline in (10, 9):
            with self.subTest(deadline=deadline):
                result = create_request(
                    central,
                    command_id=f"COMMAND-{deadline}",
                    submitted_at=10,
                    deadline=deadline,
                )
                self.assertEqual(result.status, "rejected")
                self.assertEqual(result.reason, "invalid_input")
        self.assertEqual(central.get_history("MISSION-1").value, ())

    def test_response_send_time_before_submission_is_rejected(self):
        central = registered_central()
        created = create_request(central, submitted_at=10)

        response = respond(
            central,
            created.value.request_id,
            sent_at=9,
            received_at=11,
        )

        self.assertEqual(response.status, "rejected")
        self.assertEqual(response.reason, "invalid_input")
        self.assertEqual(central.get_progress("MISSION-1", now=11).value.pending, 3)
        self.assertEqual(len(central.get_history("MISSION-1").value), 1)

    def test_cancellation_before_delivery_keeps_receipt_unknown_and_cannot_reopen(self):
        central = registered_central()
        created = create_request(central, deadline=20)
        cancelled = central.cancel_request(
            CancelRequest(
                mission_id="MISSION-1",
                request_id=created.value.request_id,
                now=12,
                reason="mission no longer needs this ship",
            )
        )
        self.assertEqual(cancelled.status, "applied")
        self.assertIsNone(cancelled.value.response_received_at)
        self.assertIsNone(timing(cancelled.value, now=13).response_elapsed_seconds)

        late = respond(
            central,
            created.value.request_id,
            message_id="MESSAGE-AFTER-CANCEL",
            delivery_id="DELIVERY-AFTER-CANCEL",
            sent_at=13,
            received_at=14,
        )

        self.assertEqual(late.status, "ignored")
        self.assertEqual(late.reason, "closed_request")
        self.assertEqual(late.value.outcome, "cancelled")
        self.assertIsNone(late.value.response_received_at)
        self.assertEqual(central.get_progress("MISSION-1", now=14).value.confirmed, 0)
        self.assertEqual(len(central.get_history("MISSION-1").value), 2)

    def test_receipt_at_or_after_deadline_expires_before_acceptance_and_releases_demand(self):
        for receipt_time in (20, 21):
            with self.subTest(receipt_time=receipt_time):
                central = registered_central()
                created = create_request(central, deadline=20)

                late = respond(
                    central,
                    created.value.request_id,
                    message_id=f"MESSAGE-LATE-{receipt_time}",
                    delivery_id=f"DELIVERY-LATE-{receipt_time}",
                    sent_at=19,
                    received_at=receipt_time,
                )

                self.assertEqual(late.status, "ignored")
                self.assertEqual(late.reason, "late")
                self.assertEqual(late.value.outcome, "expired")
                self.assertEqual(
                    central.get_progress("MISSION-1", now=receipt_time).value.pending, 0
                )
                self.assertEqual(
                    central.get_progress("MISSION-1", now=receipt_time).value.additional_needed, 6
                )

                replacement = create_request(
                    central,
                    command_id="COMMAND-REPLACEMENT",
                    submitted_at=receipt_time + 1,
                )
                self.assertEqual(replacement.status, "applied")
                self.assertEqual(
                    central.get_progress("MISSION-1", now=receipt_time + 1).value.pending, 3
                )

                later_delivery = respond(
                    central,
                    created.value.request_id,
                    message_id=f"MESSAGE-TOO-LATE-{receipt_time}",
                    delivery_id=f"DELIVERY-TOO-LATE-{receipt_time}",
                    sent_at=receipt_time + 1,
                    received_at=receipt_time + 2,
                )
                self.assertEqual(later_delivery.status, "ignored")
                self.assertEqual(later_delivery.reason, "late")
                self.assertEqual(
                    central.get_progress("MISSION-1", now=receipt_time + 2).value.pending, 3
                )


if __name__ == "__main__":
    unittest.main()
