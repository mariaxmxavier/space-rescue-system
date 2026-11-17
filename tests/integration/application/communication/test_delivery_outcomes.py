import unittest

from rescue.application.contracts import (
    CancelRequest,
    CreateRequest,
    ExpireRequest,
    PublishAvailability,
    PublishOffer,
    RecordResponse,
    RegisterMission,
    RegisterShip,
)
from rescue.bootstrap import new_run
from rescue.market.models.availability import ShipAvailability
from rescue.market.models.offers import ShipOfferRevision


def _setup(*, deadline=None, submitted_at=0):
    central = new_run("RUN-OUTCOMES", "CENTRAL-OUTCOMES").central
    central.register_mission(RegisterMission("MISSION-1", "Station", 2, 0))
    central.register_ship(RegisterShip("SHIP-1", "Rescue One"))
    central.publish_availability(
        PublishAvailability(ShipAvailability("AVAIL-1", "SHIP-1", 4, 5, True, 0))
    )
    central.publish_offer(
        PublishOffer("OFFER-1", "MISSION-1", "SHIP-1", ShipOfferRevision("REV-1", 1, 4, 5, True, 0))
    )
    created = central.create_request(
        CreateRequest(
            command_id="COMMAND-1",
            mission_id="MISSION-1",
            ship_id="SHIP-1",
            requested_seats=1,
            revision_id="REV-1",
            now=submitted_at,
            response_deadline=deadline,
        )
    )
    return central, created.value.request_id


def _send(central, request_id, *, message="MSG-1", delivery="DEL-1", attempt=1, **overrides):
    fields = {
        "outcome": "accepted",
        "confirmed_seats": 1,
        "sent_at": 1,
        "received_at": 2,
    }
    fields.update(overrides)
    return central.record_response(
        RecordResponse(
            message_id=message,
            delivery_id=delivery,
            attempt_number=attempt,
            request_id=request_id,
            **fields,
        )
    )


def _deliveries(central, message="MSG-1"):
    result = central.get_deliveries(message)
    return result.value if result.status == "applied" else ()


def _seats(central):
    progress = central.get_progress("MISSION-1", 100).value
    return progress.confirmed, progress.pending


class DeliveryOutcomeTests(unittest.TestCase):
    def assert_outcome(self, result, status, reason):
        self.assertEqual((result.status, result.reason), (status, reason))

    def assert_delivery(self, central, disposition, reason, *, message="MSG-1", count=1):
        deliveries = _deliveries(central, message)
        self.assertEqual(len(deliveries), count)
        self.assertEqual((deliveries[-1].disposition, deliveries[-1].reason), (disposition, reason))

    def test_row1_identical_known_delivery_is_ignored_without_new_record(self):
        """An identical known delivery is ignored and adds no record or history."""
        central, request_id = _setup()
        _send(central, request_id)
        history = len(central.get_history("MISSION-1").value)

        result = _send(central, request_id)

        self.assert_outcome(result, "ignored", None)
        self.assert_delivery(central, "applied", "response_applied")
        self.assertEqual(len(central.get_history("MISSION-1").value), history)
        self.assertEqual(_seats(central), (1, 0))

    def test_row2_known_delivery_with_different_content_conflicts_without_record(self):
        """A known delivery id reused with another attempt conflicts and adds no record."""
        central, request_id = _setup()
        _send(central, request_id)

        result = _send(central, request_id, attempt=2)

        self.assert_outcome(result, "rejected", "identity_conflict")
        self.assert_delivery(central, "applied", "response_applied")
        self.assertEqual(_seats(central), (1, 0))

    def test_row2_reused_delivery_identity_with_same_message_id_conflicts(self):
        """A delivery id reused with the same message id but other content conflicts."""
        central, request_id = _setup()
        _send(central, request_id)

        result = _send(central, request_id, outcome="refused", confirmed_seats=0)

        self.assert_outcome(result, "rejected", "identity_conflict")
        self.assert_delivery(central, "applied", "response_applied")
        self.assertEqual(_seats(central), (1, 0))

    def test_row4_message_conflict_is_recorded_as_rejected_and_changes_no_seats(self):
        """A new delivery of an existing message id with other content is rejected."""
        central, request_id = _setup()
        _send(central, request_id, received_at=None)

        result = _send(central, request_id, delivery="DEL-2", outcome="refused", confirmed_seats=0)

        self.assert_outcome(result, "rejected", "identity_conflict")
        self.assert_delivery(central, "rejected", "identity_conflict", count=2)
        self.assertEqual(_seats(central), (0, 1))

    def test_row5a_unknown_request_without_receipt_is_lost(self):
        """An unknown request without receipt is recorded lost and applied."""
        central, _ = _setup()

        result = _send(central, "MISSING", received_at=None)

        self.assert_outcome(result, "applied", None)
        self.assert_delivery(central, "lost", "transport_loss")
        self.assertEqual(_seats(central), (0, 1))

    def test_row5b_unknown_request_with_receipt_is_ignored(self):
        """An unknown request with receipt is recorded ignored as unknown_request."""
        central, _ = _setup()

        result = _send(central, "MISSING")

        self.assert_outcome(result, "ignored", "unknown_request")
        self.assert_delivery(central, "ignored", "unknown_request")
        self.assertEqual(_seats(central), (0, 1))

    def test_row6_send_before_submission_is_rejected_as_invalid_input(self):
        """A response sent before its request was submitted is rejected as invalid input."""
        central, request_id = _setup(submitted_at=5)

        result = _send(central, request_id, sent_at=3, received_at=6)

        self.assert_outcome(result, "rejected", "invalid_input")
        self.assert_delivery(central, "rejected", "invalid_input")
        self.assertEqual(_seats(central), (0, 1))

    def test_row7_missing_receipt_is_lost_and_leaves_request_pending(self):
        """A response without receipt is recorded lost and the request stays pending."""
        central, request_id = _setup()

        result = _send(central, request_id, received_at=None)

        self.assert_outcome(result, "applied", None)
        self.assert_delivery(central, "lost", "transport_loss")
        self.assertEqual(_seats(central), (0, 1))

    def test_row8a_response_at_deadline_after_expiry_is_late(self):
        """A response received exactly at the deadline of an expired request is late."""
        central, request_id = _setup(deadline=10)
        central.expire_request(ExpireRequest("MISSION-1", request_id, 10))

        result = _send(central, request_id, sent_at=5, received_at=10)

        self.assert_outcome(result, "ignored", "late")
        self.assert_delivery(central, "late", "deadline_expired")
        self.assertEqual(_seats(central), (0, 0))

    def test_row8b_response_for_cancelled_request_is_ignored_as_closed(self):
        """A response for a cancelled request is ignored as closed_request."""
        central, request_id = _setup()
        central.cancel_request(CancelRequest("MISSION-1", request_id, 2, "no longer needed"))

        result = _send(central, request_id, sent_at=3, received_at=4)

        self.assert_outcome(result, "ignored", "closed_request")
        self.assert_delivery(central, "ignored", "closed_request")
        self.assertEqual(_seats(central), (0, 0))

    def test_row9_response_at_deadline_expires_open_request_then_records_late(self):
        """A response received exactly at the deadline of an open request expires it as late."""
        central, request_id = _setup(deadline=10)

        result = _send(central, request_id, sent_at=5, received_at=10)

        self.assert_outcome(result, "ignored", "late")
        self.assert_delivery(central, "late", "deadline_expired")
        self.assertEqual(_seats(central), (0, 0))

    def test_row9_response_before_deadline_is_applied(self):
        """A response received just before the deadline is applied normally."""
        central, request_id = _setup(deadline=10)

        result = _send(central, request_id, sent_at=5, received_at=9)

        self.assert_outcome(result, "applied", None)
        self.assert_delivery(central, "applied", "response_applied")
        self.assertEqual(_seats(central), (1, 0))

    def test_row10_mission_rule_error_is_recorded_rejected_with_mapped_reason(self):
        """A mission-rule error while applying records a rejection with the mapped reason."""
        central, request_id = _setup()

        result = _send(central, request_id, confirmed_seats=5)

        self.assert_outcome(result, "rejected", "invalid_input")
        self.assert_delivery(central, "rejected", "invalid_input")
        self.assertEqual(_seats(central), (0, 1))

    def test_row11_normal_response_is_applied(self):
        """A normal open-request response is applied and confirms seats."""
        central, request_id = _setup()

        result = _send(central, request_id)

        self.assert_outcome(result, "applied", None)
        self.assertEqual(result.value.confirmed_seats, 1)
        self.assert_delivery(central, "applied", "response_applied")
        self.assertEqual(_seats(central), (1, 0))

    def test_story1_lost_attempt_then_new_delivery_applies_at_most_once(self):
        """A message lost then redelivered under a new delivery id affects seats once."""
        central, request_id = _setup()
        _send(central, request_id, received_at=None)

        applied = _send(central, request_id, delivery="DEL-2", attempt=2)
        again = _send(central, request_id, delivery="DEL-3", attempt=3)

        self.assert_outcome(applied, "applied", None)
        self.assert_outcome(again, "ignored", "closed_request")
        self.assertEqual(
            [item.disposition for item in _deliveries(central)],
            ["lost", "applied", "ignored"],
        )
        self.assertEqual(_seats(central), (1, 0))

    def test_new_attempt_for_applied_message_changes_no_seats(self):
        """A new delivery attempt of an already applied message changes no seats or history."""
        central, request_id = _setup()
        _send(central, request_id)
        history = len(central.get_history("MISSION-1").value)

        result = _send(central, request_id, delivery="DEL-2", attempt=2)

        self.assert_outcome(result, "ignored", "closed_request")
        self.assertEqual(len(central.get_history("MISSION-1").value), history)
        self.assertEqual(_seats(central), (1, 0))


if __name__ == "__main__":
    unittest.main()
