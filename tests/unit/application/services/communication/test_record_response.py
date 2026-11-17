import unittest
from collections import Counter

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
from rescue.application.services.communication.record_response import record_response
from rescue.bootstrap import new_run
from rescue.communication.models import FlowDirection, SessionEnvelope
from rescue.market.models.availability import ShipAvailability
from rescue.market.models.offers import ShipOfferRevision
from tests.unit.application.services.fakes import FakeIds, FakeStore

SESSION = "SESSION-1"


def _run(*, deadline=None):
    ids = FakeIds()
    context = new_run("RUN-RESPONSE", "CENTRAL-RESPONSE", id_source=ids)
    central = context.central
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
            now=0,
            response_deadline=deadline,
        )
    )
    return context, ids, created.value.request_id


def _command(request_id, *, message="MSG-1", delivery="DEL-1", version=None, sequence=1, **extra):
    fields = {
        "outcome": "accepted",
        "confirmed_seats": 1,
        "sent_at": 1,
        "received_at": 2,
    }
    fields.update(extra)
    envelope = (
        None
        if version is None
        else SessionEnvelope(SESSION, version, FlowDirection.INBOUND, sequence)
    )
    return RecordResponse(
        message_id=message,
        delivery_id=delivery,
        attempt_number=1,
        request_id=request_id,
        envelope=envelope,
        **fields,
    )


def _state(context):
    return context.store.transact(lambda state: (state, state))


def _compare(case, context, ids, command):
    before = _state(context)
    store = FakeStore(before)
    new_ids = FakeIds()
    new_ids.counts = Counter(ids.counts)
    new_result = record_response(command, store=store, id_source=new_ids)
    old_result = context.central.record_response(command)
    case.assertEqual(new_result, old_result)
    case.assertEqual(store.state, _state(context))
    case.assertEqual(new_ids.counts, ids.counts)
    return new_result, before, store.state, new_ids


class RecordResponseBranchTests(unittest.TestCase):
    def test_known_identical_delivery_returns_the_ignored_result_and_leaves_state(self):
        """Branch one: decision none returns before the session step, state unchanged."""
        context, ids, request_id = _run()
        context.central.record_response(_command(request_id))

        result, before, after, _ = _compare(self, context, ids, _command(request_id))

        self.assertEqual((result.status, result.reason), ("ignored", None))
        self.assertIs(after, before)

    def test_duplicate_sequence_is_recorded_ignored_without_a_report(self):
        """Branch two: a repeated session sequence is ignored as duplicate_sequence."""
        context, ids, request_id = _run()
        context.central.record_response(_command(request_id, version=1, sequence=1))

        result, before, after, _ = _compare(
            self, context, ids, _command(request_id, message="MSG-2", delivery="DEL-2", version=1)
        )

        self.assertEqual((result.status, result.reason), ("ignored", "duplicate_sequence"))
        self.assertEqual(len(after.delivery_index), len(before.delivery_index) + 1)
        self.assertEqual(after.delivery_index[-1][2].reason, "duplicate_sequence")

    def test_record_decision_publishes_without_changing_the_mission(self):
        """Branch three: a late response for an expired request is recorded only."""
        context, ids, request_id = _run(deadline=10)
        context.central.expire_request(ExpireRequest("MISSION-1", request_id, 10))

        result, before, after, new_ids = _compare(
            self, context, ids, _command(request_id, sent_at=5, received_at=10)
        )

        self.assertEqual((result.status, result.reason), ("ignored", "late"))
        self.assertEqual(after.missions, before.missions)
        self.assertEqual(after.delivery_index[-1][2].disposition, "late")

    def test_closed_request_is_recorded_ignored(self):
        """Branch three: a cancelled request records the delivery as closed_request."""
        context, ids, request_id = _run()
        context.central.cancel_request(CancelRequest("MISSION-1", request_id, 2, "no need"))

        result, _before, _after, _ = _compare(
            self, context, ids, _command(request_id, sent_at=3, received_at=4)
        )

        self.assertEqual((result.status, result.reason), ("ignored", "closed_request"))

    def test_deadline_response_expires_the_request_with_one_event_id_then_records(self):
        """Branch four: receipt at the deadline expires the request first."""
        context, ids, request_id = _run(deadline=10)
        events_before = ids.counts["event"]

        result, before, after, new_ids = _compare(
            self, context, ids, _command(request_id, sent_at=5, received_at=10)
        )

        self.assertEqual((result.status, result.reason), ("ignored", "late"))
        self.assertEqual(new_ids.counts["event"], events_before + 1)
        self.assertNotEqual(after.missions, before.missions)
        self.assertEqual(after.delivery_index[-1][2].reason, "deadline_expired")

    def test_normal_response_applies_the_outcome(self):
        """Branch five: an open request accepts the response and confirms its seats."""
        context, ids, request_id = _run()

        result, _before, after, _ = _compare(self, context, ids, _command(request_id))

        self.assertEqual((result.status, result.value.confirmed_seats), ("applied", 1))
        self.assertEqual(after.delivery_index[-1][2].reason, "response_applied")

    def test_mission_rule_error_is_recorded_rejected_with_the_mapped_reason(self):
        """Branch five error: apply_outcome failing records the rejection and keeps the mission."""
        context, ids, request_id = _run()

        result, before, after, _ = _compare(
            self, context, ids, _command(request_id, confirmed_seats=5)
        )

        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))
        self.assertEqual(after.missions, before.missions)
        self.assertEqual(after.delivery_index[-1][2].disposition, "rejected")

    def test_stale_session_is_rejected_and_state_is_unchanged(self):
        """The stale verdict returns rejected/stale_session before anything is published."""
        context, ids, request_id = _run()
        context.central.record_response(_command(request_id, version=2))

        result, before, after, _ = _compare(
            self,
            context,
            ids,
            _command(request_id, message="MSG-OLD", delivery="DEL-OLD", version=1),
        )

        self.assertEqual((result.status, result.reason), ("rejected", "stale_session"))
        self.assertIs(after, before)

    def test_receipt_before_send_is_rejected_by_the_outer_handler(self):
        """A normalisation error maps to rejected with the state unchanged."""
        context, ids, request_id = _run()

        result, before, after, _ = _compare(
            self, context, ids, _command(request_id, sent_at=5, received_at=3)
        )

        self.assertEqual((result.status, result.reason), ("rejected", "invalid_input"))
        self.assertIs(after, before)

    def test_type_error_is_rejected_by_the_outer_handler(self):
        """A TypeError from a wrongly typed envelope maps to rejected, state unchanged."""
        context, ids, request_id = _run()
        command = _command(request_id)
        object.__setattr__(command, "envelope", "not-an-envelope")

        result, before, after, _ = _compare(self, context, ids, command)

        self.assertEqual(result.status, "rejected")
        self.assertIs(after, before)


if __name__ == "__main__":
    unittest.main()
