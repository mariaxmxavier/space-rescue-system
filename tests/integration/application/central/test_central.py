"""Callable integration checks for run-local central state and retries."""

import unittest

from rescue.application.contracts import (
    AcceptQuote,
    CancelRequest,
    CreateRequest,
    Mobilise,
    PublishAvailability,
    PublishOffer,
    RecordQuote,
    RecordResponse,
    RegisterMission,
    RegisterShip,
    RequestQuotes,
)
from rescue.bootstrap import new_run
from rescue.market.models import RFQOffer, ShipAvailability, ShipOfferRevision
from rescue.market.rules import usage
from rescue.mobilisation.models import MobilisationPolicy


def register_mission(central, mission_id, people_count=5):
    return central.register_mission(
        RegisterMission(
            mission_id=mission_id,
            station_name=f"Station {mission_id}",
            people_count=people_count,
            created_at=0,
        )
    )


def register_ship(central, total_seats=6):
    central.register_ship(RegisterShip(ship_id="SHIP-1", name="Rescue One"))
    central.publish_availability(
        PublishAvailability(
            availability=ShipAvailability(
                availability_id="AVAIL-1",
                ship_id="SHIP-1",
                total_seats=total_seats,
                arrival_estimate_seconds=10,
                available=True,
                recorded_at=0,
            )
        )
    )


def publish_offer(central, mission_id, capacity=6):
    central.publish_offer(
        PublishOffer(
            offer_id=f"OFFER-{mission_id}",
            mission_id=mission_id,
            ship_id="SHIP-1",
            revision=ShipOfferRevision(
                revision_id=f"REV-{mission_id}",
                revision_number=1,
                capacity=capacity,
                arrival_estimate_seconds=10,
                available=True,
                recorded_at=0,
            ),
        )
    )


class CentralRunTests(unittest.TestCase):
    def test_run_has_one_central_and_missions_retain_independent_history(self):
        run = new_run("RUN-1", "CENTRAL-1")
        central = run.central

        self.assertIs(run.central, central)
        register_mission(central, "MISSION-A")
        register_mission(central, "MISSION-B")
        register_ship(central)
        publish_offer(central, "MISSION-A")
        publish_offer(central, "MISSION-B")

        for mission_id in ("MISSION-A", "MISSION-B"):
            result = central.create_request(
                CreateRequest(
                    command_id=f"COMMAND-{mission_id}",
                    mission_id=mission_id,
                    ship_id="SHIP-1",
                    requested_seats=3,
                    revision_id=f"REV-{mission_id}",
                    now=1,
                )
            )
            self.assertEqual(result.status, "applied")
            self.assertEqual(
                central.get_progress(mission_id, now=2).value.pending,
                3,
            )
            self.assertEqual(len(central.get_history(mission_id).value), 1)

        self.assertEqual(central.get_progress("MISSION-A", now=2).value.pending, 3)
        self.assertEqual(central.get_progress("MISSION-B", now=2).value.pending, 3)

        fresh = new_run("RUN-2", "CENTRAL-2").central
        self.assertEqual(fresh.get_progress("MISSION-A", now=2).reason, "unknown_mission")
        self.assertEqual(fresh.get_history("MISSION-A").reason, "unknown_mission")

        duplicate = register_mission(central, "MISSION-A", people_count=9)
        self.assertEqual(duplicate.status, "rejected")
        self.assertEqual(duplicate.reason, "identity_conflict")
        self.assertEqual(central.get_progress("MISSION-A", now=2).value.demand, 5)

    def test_create_request_retry_replays_and_changed_payload_conflicts(self):
        central = new_run("RUN-1", "CENTRAL-1").central
        register_mission(central, "MISSION-1")
        register_ship(central)
        publish_offer(central, "MISSION-1")
        command = CreateRequest(
            command_id="COMMAND-1",
            mission_id="MISSION-1",
            ship_id="SHIP-1",
            requested_seats=3,
            revision_id="REV-MISSION-1",
            now=1,
        )

        applied = central.create_request(command)
        closed = central.record_response(
            RecordResponse(
                message_id="MESSAGE-1",
                delivery_id="DELIVERY-1",
                attempt_number=1,
                request_id=applied.value.request_id,
                outcome="accepted",
                confirmed_seats=3,
                sent_at=2,
                received_at=2,
            )
        )
        replay = central.create_request(
            CreateRequest(
                command_id=command.command_id,
                mission_id=command.mission_id,
                ship_id=command.ship_id,
                requested_seats=command.requested_seats,
                revision_id=command.revision_id,
                now=9,
            )
        )
        conflict = central.create_request(
            CreateRequest(
                command_id=command.command_id,
                mission_id=command.mission_id,
                ship_id=command.ship_id,
                requested_seats=2,
                revision_id=command.revision_id,
                now=9,
            )
        )

        self.assertEqual(closed.status, "applied")
        self.assertEqual(replay.status, "replayed")
        self.assertEqual(replay.value, applied.value)
        self.assertEqual(conflict.status, "rejected")
        self.assertEqual(conflict.reason, "identity_conflict")
        self.assertEqual(len(central.get_history("MISSION-1").value), 2)
        self.assertEqual(central.get_progress("MISSION-1", now=9).value.confirmed, 3)

    def test_unknown_request_delivery_is_diagnostic_without_business_mutation(self):
        central = new_run("RUN-1", "CENTRAL-1").central
        register_mission(central, "MISSION-1", people_count=4)
        before_progress = central.get_progress("MISSION-1", now=1).value
        before_history = central.get_history("MISSION-1").value

        result = central.record_response(
            RecordResponse(
                message_id="MESSAGE-UNKNOWN",
                delivery_id="DELIVERY-UNKNOWN",
                attempt_number=1,
                request_id="MISSING-REQUEST",
                outcome="accepted",
                confirmed_seats=1,
                sent_at=1,
                received_at=1,
            )
        )

        self.assertEqual(result.status, "ignored")
        self.assertEqual(result.reason, "unknown_request")
        self.assertEqual(central.get_progress("MISSION-1", now=1).value, before_progress)
        self.assertEqual(central.get_history("MISSION-1").value, before_history)
        diagnostic_counts = central.store.transact(
            lambda state: (state, (len(state.message_index), len(state.delivery_index)))
        )
        self.assertEqual(diagnostic_counts, (1, 1))

    def test_capacity_revision_does_not_rewrite_existing_request_or_allow_shortfall_growth(self):
        central = new_run("RUN-1", "CENTRAL-1").central
        register_mission(central, "MISSION-1", people_count=20)
        register_ship(central, total_seats=30)
        publish_offer(central, "MISSION-1", capacity=30)
        created = central.create_request(
            CreateRequest(
                command_id="COMMAND-1",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                requested_seats=15,
                revision_id="REV-MISSION-1",
                now=1,
            )
        )
        self.assertEqual(created.status, "applied")
        original_request = created.value

        reduced = ShipAvailability(
            availability_id="AVAIL-REDUCED",
            ship_id="SHIP-1",
            total_seats=10,
            arrival_estimate_seconds=12,
            available=True,
            recorded_at=2,
        )
        self.assertEqual(
            central.publish_availability(PublishAvailability(reduced)).status, "applied"
        )
        stored_request = central.store.transact(
            lambda state: (
                state,
                next(
                    request
                    for mission in state.missions
                    for request in mission.requests
                    if request.request_id == original_request.request_id
                ),
            )
        )
        self.assertEqual(stored_request, original_request)
        ship_usage = central.store.transact(
            lambda state: (state, usage(state.market, state.missions, "SHIP-1"))
        )
        self.assertEqual((ship_usage.used, ship_usage.total, ship_usage.shortfall), (15, 10, 5))

        blocked = central.create_request(
            CreateRequest(
                command_id="COMMAND-2",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                requested_seats=1,
                revision_id="REV-MISSION-1",
                now=3,
            )
        )
        self.assertEqual(blocked.status, "rejected")
        self.assertEqual(blocked.reason, "insufficient_capacity")
        self.assertEqual(len(central.get_history("MISSION-1").value), 1)

    def test_highest_revision_number_wins_despite_reverse_recorded_times(self):
        central = new_run("RUN-1", "CENTRAL-1").central
        register_mission(central, "MISSION-1")
        register_ship(central)
        first = ShipOfferRevision(
            revision_id="REV-1",
            revision_number=1,
            capacity=4,
            arrival_estimate_seconds=20,
            available=True,
            recorded_at=100,
        )
        second = ShipOfferRevision(
            revision_id="REV-2",
            revision_number=2,
            capacity=6,
            arrival_estimate_seconds=10,
            available=True,
            recorded_at=10,
        )
        central.publish_offer(
            PublishOffer(
                offer_id="OFFER-MISSION-1",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                revision=first,
            )
        )
        central.publish_offer(
            PublishOffer(
                offer_id="OFFER-MISSION-1",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                revision=second,
            )
        )

        current = central.store.transact(
            lambda state: (state, state.market.offers[0].current_revision)
        )
        self.assertEqual(current, second)

    def test_command_identity_cannot_be_reused_for_a_different_mission(self):
        central = new_run("RUN-1", "CENTRAL-1").central
        register_mission(central, "MISSION-A")
        register_mission(central, "MISSION-B")
        register_ship(central)
        publish_offer(central, "MISSION-A")
        publish_offer(central, "MISSION-B")
        first = central.create_request(
            CreateRequest(
                command_id="SHARED-COMMAND",
                mission_id="MISSION-A",
                ship_id="SHIP-1",
                requested_seats=2,
                revision_id="REV-MISSION-A",
                now=1,
            )
        )
        second = central.create_request(
            CreateRequest(
                command_id="SHARED-COMMAND",
                mission_id="MISSION-B",
                ship_id="SHIP-1",
                requested_seats=2,
                revision_id="REV-MISSION-B",
                now=1,
            )
        )

        self.assertEqual(first.status, "applied")
        self.assertEqual(second.status, "rejected")
        self.assertEqual(second.reason, "identity_conflict")
        self.assertEqual(central.get_history("MISSION-B").value, ())

    def test_quote_backed_retry_replays_after_response_and_expiry_time(self):
        central = new_run("RUN-1", "CENTRAL-1").central
        register_mission(central, "MISSION-1", people_count=3)
        register_ship(central)
        publish_offer(central, "MISSION-1")
        rfq = central.request_quotes(RequestQuotes(mission_id="MISSION-1", now=1)).value[0]
        quote = RFQOffer(
            offer_id="QUOTE-1",
            rfq_id=rfq.rfq_id,
            offered_seats=3,
            arrival_estimate_seconds=10,
            expires_at=5,
            recorded_at=2,
        )
        central.record_quote(RecordQuote(offer=quote, now=2))
        command = AcceptQuote(
            command_id="ACCEPT-1",
            mission_id="MISSION-1",
            quote_id="QUOTE-1",
            now=4,
        )
        accepted = central.accept_quote(command)
        self.assertEqual(accepted.status, "applied")
        closed = central.record_response(
            RecordResponse(
                message_id="MESSAGE-1",
                delivery_id="DELIVERY-1",
                attempt_number=1,
                request_id=accepted.value.request_id,
                outcome="accepted",
                confirmed_seats=3,
                sent_at=4,
                received_at=4,
            )
        )
        history_before = central.get_history("MISSION-1").value

        replay = central.accept_quote(
            AcceptQuote(
                command_id=command.command_id,
                mission_id=command.mission_id,
                quote_id=command.quote_id,
                now=6,
            )
        )

        self.assertEqual(closed.status, "applied")
        self.assertEqual(replay.status, "replayed")
        self.assertEqual(replay.value, accepted.value)
        self.assertEqual(central.get_history("MISSION-1").value, history_before)

    def test_failed_quote_transfer_preserves_hold_request_history_and_command_identity(self):
        central = new_run("RUN-1", "CENTRAL-1").central
        register_mission(central, "MISSION-1", people_count=3)
        register_ship(central)
        publish_offer(central, "MISSION-1")
        rfq = central.request_quotes(RequestQuotes(mission_id="MISSION-1", now=1)).value[0]
        quote = RFQOffer(
            offer_id="QUOTE-1",
            rfq_id=rfq.rfq_id,
            offered_seats=3,
            arrival_estimate_seconds=10,
            expires_at=100,
            recorded_at=2,
            status="held",
        )
        recorded = central.record_quote(RecordQuote(offer=quote, now=2))
        self.assertEqual(recorded.status, "applied")
        self.assertEqual(central.get_progress("MISSION-1", now=2).value.pending, 0)
        held_usage = central.store.transact(
            lambda state: (state, usage(state.market, state.missions, "SHIP-1"))
        )
        self.assertEqual(held_usage.held, 3)
        self.assertEqual(held_usage.pending, 0)
        self.assertEqual(held_usage.confirmed, 0)

        pending = central.create_request(
            CreateRequest(
                command_id="DIRECT-1",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                requested_seats=1,
                revision_id="REV-MISSION-1",
                now=3,
            )
        )
        before_progress = central.get_progress("MISSION-1", now=3).value
        before_history = central.get_history("MISSION-1").value
        transfer = AcceptQuote(
            command_id="ACCEPT-1",
            mission_id="MISSION-1",
            quote_id="QUOTE-1",
            now=4,
        )

        failed = central.accept_quote(transfer)

        self.assertEqual(failed.status, "rejected")
        self.assertEqual(failed.reason, "insufficient_demand")
        self.assertEqual(central.get_progress("MISSION-1", now=4).value, before_progress)
        self.assertEqual(central.get_history("MISSION-1").value, before_history)

        central.cancel_request(
            CancelRequest(
                mission_id="MISSION-1",
                request_id=pending.value.request_id,
                now=5,
                reason="make room for the held quote",
            )
        )
        transferred = central.accept_quote(
            AcceptQuote(
                command_id=transfer.command_id,
                mission_id=transfer.mission_id,
                quote_id=transfer.quote_id,
                now=6,
            )
        )
        self.assertEqual(transferred.status, "applied")
        self.assertEqual(transferred.value.requested_seats, 3)

    def test_mobilise_records_a_proposal_without_reserving_capacity(self):
        policy = MobilisationPolicy(
            policy_id="EARLIEST",
            revision=1,
            name="Earliest arrival",
            selection_criteria="earliest_arrival",
        )
        run = new_run("RUN-1", "CENTRAL-1", policies=(policy,))
        central = run.central
        register_mission(central, "MISSION-1", people_count=8)
        register_ship(central, total_seats=6)
        publish_offer(central, "MISSION-1", capacity=5)
        before = run.store.transact(
            lambda state: (state, usage(state.market, state.missions, "SHIP-1"))
        )

        proposed = central.mobilise(
            Mobilise(
                mission_id="MISSION-1",
                policy_id="EARLIEST",
                policy_revision=1,
                now=1,
            )
        )

        self.assertEqual(proposed.status, "applied")
        decision = proposed.value
        self.assertEqual(decision.evaluations[0].proposed_seats, 5)
        self.assertEqual(decision.evaluations[0].revision.revision_id, "REV-MISSION-1")
        self.assertEqual(central.get_progress("MISSION-1", now=1).value.pending, 0)
        after = run.store.transact(
            lambda state: (state, usage(state.market, state.missions, "SHIP-1"))
        )
        self.assertEqual(before, after)

        request = central.create_request(
            CreateRequest(
                command_id="COMMAND-FROM-DECISION",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                requested_seats=5,
                revision_id="REV-MISSION-1",
                decision_id=decision.decision_id,
                now=2,
            )
        )
        self.assertEqual(request.status, "applied")
        self.assertEqual(central.get_progress("MISSION-1", now=2).value.pending, 5)
        final_usage = run.store.transact(
            lambda state: (state, usage(state.market, state.missions, "SHIP-1"))
        )
        self.assertEqual(final_usage.free, 1)

    def test_multiple_direct_requests_can_use_one_ship_without_exceeding_demand(self):
        central = new_run("RUN-1", "CENTRAL-1").central
        register_mission(central, "MISSION-1", people_count=5)
        register_ship(central, total_seats=6)
        publish_offer(central, "MISSION-1", capacity=5)

        first = central.create_request(
            CreateRequest(
                command_id="COMMAND-1",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                requested_seats=2,
                revision_id="REV-MISSION-1",
                now=1,
            )
        )
        second = central.create_request(
            CreateRequest(
                command_id="COMMAND-2",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                requested_seats=3,
                revision_id="REV-MISSION-1",
                now=2,
            )
        )

        self.assertEqual(first.status, "applied")
        self.assertEqual(second.status, "applied")
        self.assertEqual(central.get_progress("MISSION-1", now=3).value.pending, 5)
        self.assertEqual(len(central.get_history("MISSION-1").value), 2)

    def test_receipt_at_deadline_expires_before_response_and_later_delivery_is_ignored(self):
        central = new_run("RUN-1", "CENTRAL-1").central
        register_mission(central, "MISSION-1", people_count=3)
        register_ship(central, total_seats=3)
        publish_offer(central, "MISSION-1", capacity=3)
        created = central.create_request(
            CreateRequest(
                command_id="COMMAND-1",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                requested_seats=3,
                revision_id="REV-MISSION-1",
                now=1,
                response_deadline=5,
            )
        )

        at_deadline = central.record_response(
            RecordResponse(
                message_id="MESSAGE-LATE",
                delivery_id="DELIVERY-LATE",
                attempt_number=1,
                request_id=created.value.request_id,
                outcome="accepted",
                confirmed_seats=3,
                sent_at=4,
                received_at=5,
            )
        )

        self.assertEqual(at_deadline.status, "ignored")
        self.assertEqual(at_deadline.reason, "late")
        self.assertEqual(at_deadline.value.outcome, "expired")
        self.assertEqual(central.get_progress("MISSION-1", now=5).value.confirmed, 0)
        self.assertEqual(len(central.get_history("MISSION-1").value), 2)
        after_close = central.record_response(
            RecordResponse(
                message_id="MESSAGE-SECOND",
                delivery_id="DELIVERY-SECOND",
                attempt_number=1,
                request_id=created.value.request_id,
                outcome="accepted",
                confirmed_seats=3,
                sent_at=5,
                received_at=6,
            )
        )
        self.assertEqual(after_close.status, "ignored")
        self.assertEqual(after_close.reason, "late")
        self.assertEqual(len(central.get_history("MISSION-1").value), 2)

    def test_invalid_response_is_diagnostic_without_changing_mission(self):
        central = new_run("RUN-1", "CENTRAL-1").central
        register_mission(central, "MISSION-1", people_count=3)
        register_ship(central, total_seats=3)
        publish_offer(central, "MISSION-1", capacity=3)
        created = central.create_request(
            CreateRequest(
                command_id="COMMAND-1",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                requested_seats=3,
                revision_id="REV-MISSION-1",
                now=1,
            )
        )
        history_before = central.get_history("MISSION-1").value

        invalid = central.record_response(
            RecordResponse(
                message_id="MESSAGE-INVALID",
                delivery_id="DELIVERY-INVALID",
                attempt_number=1,
                request_id=created.value.request_id,
                outcome="accepted",
                confirmed_seats=2,
                sent_at=2,
                received_at=2,
            )
        )

        self.assertEqual(invalid.status, "rejected")
        self.assertEqual(invalid.reason, "invalid_input")
        self.assertEqual(central.get_progress("MISSION-1", now=2).value.pending, 3)
        self.assertEqual(central.get_history("MISSION-1").value, history_before)
        diagnostic = central.store.transact(lambda state: (state, state.delivery_index[-1]))
        self.assertEqual(diagnostic[0], "DELIVERY-INVALID")
        self.assertEqual(diagnostic[2].disposition, "rejected")

    def test_reused_delivery_identity_with_changed_message_is_rejected(self):
        central = new_run("RUN-1", "CENTRAL-1").central
        register_mission(central, "MISSION-1", people_count=3)
        register_ship(central, total_seats=3)
        publish_offer(central, "MISSION-1", capacity=3)
        created = central.create_request(
            CreateRequest(
                command_id="COMMAND-1",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                requested_seats=3,
                revision_id="REV-MISSION-1",
                now=1,
            )
        )
        first = RecordResponse(
            message_id="MESSAGE-1",
            delivery_id="DELIVERY-1",
            attempt_number=1,
            request_id=created.value.request_id,
            outcome="accepted",
            confirmed_seats=3,
            sent_at=2,
            received_at=2,
            communication_rtt_seconds=5,
        )
        self.assertEqual(central.record_response(first).status, "applied")

        conflict = central.record_response(
            RecordResponse(
                message_id="MESSAGE-1",
                delivery_id="DELIVERY-1",
                attempt_number=1,
                request_id=created.value.request_id,
                outcome="refused",
                confirmed_seats=0,
                sent_at=2,
                received_at=2,
            )
        )

        self.assertEqual(conflict.status, "rejected")
        self.assertEqual(conflict.reason, "identity_conflict")
        self.assertEqual(central.get_progress("MISSION-1", now=2).value.confirmed, 3)

        changed_delivery = central.record_response(
            RecordResponse(
                message_id="MESSAGE-1",
                delivery_id="DELIVERY-1",
                attempt_number=1,
                request_id=created.value.request_id,
                outcome="accepted",
                confirmed_seats=3,
                sent_at=2,
                received_at=2,
                communication_rtt_seconds=6,
            )
        )
        self.assertEqual(changed_delivery.status, "rejected")
        self.assertEqual(changed_delivery.reason, "identity_conflict")

    def test_decision_snapshot_is_queryable_and_request_must_retain_selected_basis(self):
        policy = MobilisationPolicy(
            policy_id="EARLIEST",
            revision=1,
            name="Earliest arrival",
            selection_criteria="earliest_arrival",
        )
        central = new_run("RUN-1", "CENTRAL-1", policies=(policy,)).central
        register_mission(central, "MISSION-1", people_count=8)
        register_ship(central, total_seats=6)
        publish_offer(central, "MISSION-1", capacity=6)
        decision = central.mobilise(Mobilise("MISSION-1", "EARLIEST", 1, 1)).value

        self.assertEqual(central.get_decision(decision.decision_id).value, decision)
        self.assertEqual(central.get_decision("missing").reason, "unknown_decision")
        wrong_basis = central.create_request(
            CreateRequest(
                command_id="COMMAND-WRONG-BASIS",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                requested_seats=2,
                revision_id="UNLISTED-REVISION",
                decision_id=decision.decision_id,
                now=2,
            )
        )
        self.assertEqual(wrong_basis.status, "rejected")
        self.assertEqual(wrong_basis.reason, "revision_conflict")
        self.assertEqual(central.get_history("MISSION-1").value, ())

        linked = central.create_request(
            CreateRequest(
                command_id="COMMAND-LINKED",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                requested_seats=6,
                revision_id="REV-MISSION-1",
                decision_id=decision.decision_id,
                now=2,
            )
        )
        self.assertEqual(linked.status, "applied")
        self.assertEqual(linked.value.decision_id, decision.decision_id)
        self.assertEqual(linked.value.revision_id, decision.evaluations[0].revision.revision_id)

    def test_delivery_disposition_query_returns_diagnostics_without_business_history(self):
        central = new_run("RUN-1", "CENTRAL-1").central
        central.record_response(
            RecordResponse(
                message_id="MESSAGE-UNKNOWN",
                delivery_id="DELIVERY-UNKNOWN",
                attempt_number=1,
                request_id="MISSING-REQUEST",
                outcome="accepted",
                confirmed_seats=1,
                sent_at=1,
                received_at=1,
            )
        )

        deliveries = central.get_deliveries("MESSAGE-UNKNOWN")

        self.assertEqual(deliveries.status, "applied")
        self.assertEqual(len(deliveries.value), 1)
        self.assertEqual(deliveries.value[0].disposition, "ignored")
        self.assertEqual(deliveries.value[0].reason, "unknown_request")
        self.assertEqual(central.get_deliveries("MISSING-MESSAGE").reason, "unknown_message")


if __name__ == "__main__":
    unittest.main()
