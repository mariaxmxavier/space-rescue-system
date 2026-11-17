import unittest
from dataclasses import FrozenInstanceError, replace
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
from rescue.communication import models
from rescue.experiments.models import (
    CommunicationProfile,
    RescueScenario,
    RunBaseline,
    ScriptedResponse,
)
from rescue.experiments.runner import simulate
from rescue.market.models.availability import ShipAvailability
from rescue.market.models.b3_market import B3Market
from rescue.market.models.fleet import Ship
from rescue.market.models.offers import ShipOffer, ShipOfferRevision
from rescue.mission.models import MissionData, SeatRequest
from rescue.mission.rules import add_request, register, timing
from rescue.values import TransitionContext


def _simulation_scenario(
    *,
    horizon=20,
    pending=False,
    deadline=None,
    responses=(),
    profile=None,
    availability_changes=(),
    event_budget=100,
):
    mission = register(
        MissionData(
            mission_id="MISSION-1",
            station_name="Station One",
            people_count=1,
            created_at=0,
        )
    )
    if pending:
        request = SeatRequest(
            request_id="REQUEST-1",
            command_id="COMMAND-BASELINE",
            mission_id="MISSION-1",
            ship_id="SHIP-1",
            requested_seats=1,
            confirmed_seats=0,
            outcome="pending",
            submitted_at=0,
            response_deadline=deadline,
            revision_id="REVISION-1",
        )
        mission = add_request(
            mission,
            request,
            TransitionContext("EVENT-BASELINE", 0, "request_created"),
        )

    revision = ShipOfferRevision(
        revision_id="REVISION-1",
        revision_number=1,
        capacity=4,
        arrival_estimate_seconds=3,
        available=True,
        recorded_at=0,
    )
    market = B3Market(
        market_id="MARKET-1",
        ships=(Ship(ship_id="SHIP-1", name="Rescue One"),),
        availabilities=(
            ShipAvailability(
                availability_id="AVAIL-1",
                ship_id="SHIP-1",
                total_seats=4,
                arrival_estimate_seconds=3,
                available=True,
                recorded_at=0,
            ),
        ),
        offers=(
            ShipOffer(
                offer_id="OFFER-1",
                mission_id="MISSION-1",
                ship_id="SHIP-1",
                revisions=(revision,),
            ),
        ),
    )
    baseline = RunBaseline(missions=(mission,), market=market)
    return RescueScenario(
        scenario_id="SCENARIO-1",
        revision=1,
        name="Communication scenario",
        baseline=baseline,
        response_rules=tuple(responses),
        availability_changes=tuple(availability_changes),
        time_horizon_seconds=horizon,
        seed=13,
        event_budget=event_budget,
        communication_profiles=() if profile is None else (profile,),
    )


def _policy():
    from rescue.mobilisation.models import MobilisationPolicy

    return MobilisationPolicy(
        policy_id="EARLIEST",
        revision=1,
        name="Earliest arrival",
        selection_criteria="earliest_arrival",
    )


def _profile(*, outbound=0, decision=0, returning=0, loss=(), duplicate=(), reorder=()):
    return CommunicationProfile(
        profile_id="PROFILE-1",
        ship_id="SHIP-1",
        outbound_delay_seconds=outbound,
        decision_delay_seconds=decision,
        return_delay_seconds=returning,
        loss_rule=tuple(loss),
        duplication_rule=tuple(duplicate),
        reordering_rule=tuple(reorder),
    )


def _response(outcome="accepted", ordinal=1, confirmed=1):
    return ScriptedResponse(
        ship_id="SHIP-1",
        request_ordinal=ordinal,
        outcome=outcome,
        confirmed_seats=confirmed,
    )


def _central_with_pending_request(*, deadline=None):
    central = new_run("RUN-COMM", "CENTRAL-COMM").central
    central.register_mission(RegisterMission("MISSION-COMM", "Station", 1, 0))
    central.register_ship(RegisterShip("SHIP-COMM", "Rescue One"))
    central.publish_availability(
        PublishAvailability(ShipAvailability("AVAIL-COMM", "SHIP-COMM", 3, 5, True, 0))
    )
    central.publish_offer(
        PublishOffer(
            offer_id="OFFER-COMM",
            mission_id="MISSION-COMM",
            ship_id="SHIP-COMM",
            revision=ShipOfferRevision("REV-COMM", 1, 3, 5, True, 0),
        )
    )
    created = central.create_request(
        CreateRequest(
            command_id="COMMAND-COMM",
            mission_id="MISSION-COMM",
            ship_id="SHIP-COMM",
            requested_seats=1,
            revision_id="REV-COMM",
            now=0,
            response_deadline=deadline,
        )
    )
    return central, created.value


def make_message(payload):
    return models.CommunicationMessage(
        message_id="message-1",
        correlation_id="request-1",
        kind="request",
        payload=payload,
        sent_at=Decimal("1.25"),
        request_id="request-1",
    )


class CommunicationMessageTests(unittest.TestCase):
    def test_payload_is_copied_into_frozen_primitive_pairs(self):
        source = [
            ["count", 2],
            ["available", True],
            ["cost", Decimal("1.5")],
            ["note", None],
        ]

        message = make_message(source)

        self.assertEqual(
            message.payload,
            (
                ("count", 2),
                ("available", True),
                ("cost", Decimal("1.5")),
                ("note", None),
            ),
        )
        source[0][1] = 99
        source.append(["extra", "changed"])
        self.assertEqual(message.payload[0], ("count", 2))
        self.assertEqual(len(message.payload), 4)
        self.assertIsInstance(message.sent_at, Decimal)
        with self.assertRaises(TypeError):
            message.payload[0][1] = 3
        with self.assertRaises(FrozenInstanceError):
            message.kind = "changed"

    def test_payload_rejects_callables_and_arbitrary_objects(self):
        def executable_payload():
            return "not data"

        for value in (
            executable_payload,
            object(),
            Decimal("NaN"),
            Decimal("Infinity"),
        ):
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(ValueError):
                    make_message((("value", value),))

    def test_message_ids_and_sent_time_are_validated(self):
        for field, value in (
            ("message_id", "  "),
            ("correlation_id", ""),
            ("request_id", "\t"),
        ):
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    models.CommunicationMessage(
                        message_id="message-1" if field != "message_id" else value,
                        correlation_id="request-1" if field != "correlation_id" else value,
                        kind="request",
                        payload=(),
                        sent_at=Decimal("1"),
                        request_id="request-1" if field != "request_id" else value,
                    )

        for sent_at in (Decimal("-0.1"), Decimal("NaN"), Decimal("Infinity")):
            with self.subTest(sent_at=sent_at):
                with self.assertRaises(ValueError):
                    models.CommunicationMessage(
                        message_id="message-1",
                        correlation_id="request-1",
                        kind="request",
                        payload=(),
                        sent_at=sent_at,
                        request_id="request-1",
                    )

        self.assertEqual(
            models.CommunicationMessage(
                message_id="message-2",
                correlation_id="request-1",
                kind="request",
                payload=(),
                sent_at=1,
                request_id="request-1",
            ).sent_at,
            Decimal("1"),
        )


class MessageDeliveryTests(unittest.TestCase):
    def test_distinct_attempts_refer_to_the_same_logical_message(self):
        message = make_message((("outcome", "accepted"),))
        deliveries = (
            models.MessageDelivery(
                delivery_id="delivery-1",
                attempt_number=1,
                received_at=Decimal("2"),
                disposition="applied",
                reason="response_applied",
            ),
            models.MessageDelivery(
                delivery_id="delivery-2",
                attempt_number=2,
                received_at=Decimal("3"),
                disposition="applied",
                reason="response_applied",
            ),
        )
        attempts = tuple((message, delivery) for delivery in deliveries)

        self.assertEqual(
            {attempt_message.message_id for attempt_message, _ in attempts},
            {"message-1"},
        )
        self.assertEqual(
            {delivery.delivery_id for _, delivery in attempts},
            {"delivery-1", "delivery-2"},
        )
        self.assertEqual(
            {delivery.attempt_number for _, delivery in attempts},
            {1, 2},
        )

    def test_lost_attempt_defaults_to_missing_receipt(self):
        delivery = models.MessageDelivery(
            delivery_id="delivery-lost",
            attempt_number=1,
            disposition="lost",
            reason="transport_loss",
        )

        self.assertIsNone(delivery.received_at)
        self.assertEqual(delivery.disposition, "lost")
        with self.assertRaises(FrozenInstanceError):
            delivery.disposition = "applied"

    def test_delivery_ids_attempts_and_receipt_times_are_validated(self):
        for kwargs in (
            {
                "delivery_id": "",
                "attempt_number": 1,
                "disposition": "lost",
                "reason": "transport_loss",
            },
            {
                "delivery_id": "delivery-1",
                "attempt_number": 0,
                "disposition": "lost",
                "reason": "transport_loss",
            },
            {
                "delivery_id": "delivery-1",
                "attempt_number": True,
                "disposition": "lost",
                "reason": "transport_loss",
            },
            {
                "delivery_id": "delivery-1",
                "attempt_number": 1,
                "received_at": Decimal("-1"),
                "disposition": "applied",
                "reason": "response_applied",
            },
            {
                "delivery_id": "delivery-1",
                "attempt_number": 1,
                "received_at": Decimal("NaN"),
                "disposition": "applied",
                "reason": "response_applied",
            },
            {
                "delivery_id": "delivery-1",
                "attempt_number": 1,
                "received_at": Decimal("Infinity"),
                "disposition": "applied",
                "reason": "response_applied",
            },
            {
                "delivery_id": "delivery-1",
                "attempt_number": 1,
                "received_at": Decimal("1"),
                "communication_rtt_seconds": Decimal("-1"),
                "disposition": "applied",
                "reason": "response_applied",
            },
            {
                "delivery_id": "delivery-1",
                "attempt_number": 1,
                "received_at": Decimal("1"),
                "communication_rtt_seconds": Decimal("NaN"),
                "disposition": "applied",
                "reason": "response_applied",
            },
            {
                "delivery_id": "delivery-1",
                "attempt_number": 1,
                "received_at": Decimal("1"),
                "communication_rtt_seconds": Decimal("Infinity"),
                "disposition": "applied",
                "reason": "response_applied",
            },
            {
                "delivery_id": "delivery-1",
                "attempt_number": 1,
                "communication_rtt_seconds": Decimal("1"),
                "disposition": "lost",
                "reason": "transport_loss",
            },
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    models.MessageDelivery(**kwargs)


class CommunicationSimulationTests(unittest.TestCase):
    def test_baseline_message_identity_collision_does_not_reject_simulated_response(self):
        scenario = _simulation_scenario(responses=(ScriptedResponse("SHIP-1", 1, "accepted"),))
        baseline_message = models.CommunicationMessage(
            message_id="message-00000007",
            correlation_id="BASELINE-REQUEST",
            request_id="BASELINE-REQUEST",
            kind="response",
            payload=(("outcome", "accepted"),),
            sent_at=0,
        )
        baseline_delivery = models.MessageDelivery(
            delivery_id="delivery-00000009",
            attempt_number=1,
            received_at=0,
            disposition="applied",
            reason="response_applied",
        )
        scenario = replace(
            scenario,
            baseline=replace(
                scenario.baseline,
                command_index=(
                    (
                        "BASELINE-RUN",
                        "command-00000003",
                        "baseline_command",
                        (),
                        baseline_message,
                    ),
                ),
                message_index=((baseline_message, (baseline_delivery,)),),
                delivery_index=(
                    (
                        baseline_delivery.delivery_id,
                        baseline_message.message_id,
                        baseline_delivery,
                    ),
                ),
            ),
        )

        first = simulate(scenario, _policy(), run_id="RUN-COLLISION")
        repeated = simulate(scenario, _policy(), run_id="RUN-COLLISION")

        self.assertEqual(first.run.status, "completed")
        self.assertEqual(first.run.result.confirmed_seats, 1)
        self.assertEqual(first, repeated)
        self.assertIn(baseline_message, tuple(entry[0] for entry in first.message_index))
        self.assertEqual(len(first.message_index), 2)
        self.assertEqual(len(first.command_index), 2)
        self.assertEqual(len(first.delivery_index), 2)

    def test_reordering_rule_places_flagged_same_time_response_after_unmarked_response(self):
        missions = (
            register(MissionData("MISSION-A", "Station A", 1, 0)),
            register(MissionData("MISSION-B", "Station B", 1, 0)),
        )
        ship = Ship("SHIP-1", "Rescue One")
        availability = ShipAvailability("AVAIL-1", "SHIP-1", 4, 3, True, 0)
        market = B3Market(
            market_id="MARKET-1",
            ships=(ship,),
            availabilities=(availability,),
            offers=(
                ShipOffer(
                    "OFFER-A",
                    "MISSION-A",
                    "SHIP-1",
                    (ShipOfferRevision("REV-A", 1, 2, 3, True, 0),),
                ),
                ShipOffer(
                    "OFFER-B",
                    "MISSION-B",
                    "SHIP-1",
                    (ShipOfferRevision("REV-B", 1, 2, 3, True, 0),),
                ),
            ),
        )
        scenario = RescueScenario(
            scenario_id="SCENARIO-REORDER",
            revision=1,
            name="Equal-time response reorder",
            baseline=RunBaseline(missions=missions, market=market),
            response_rules=(
                ScriptedResponse("SHIP-1", 1, "refused"),
                ScriptedResponse("SHIP-1", 2, "accepted", confirmed_seats=1),
            ),
            availability_changes=(),
            time_horizon_seconds=5,
            seed=1,
            event_budget=50,
            communication_profiles=(_profile(reorder=(1,)),),
        )

        snapshot = simulate(scenario, _policy(), run_id="RUN-REORDER")

        self.assertEqual(len(snapshot.message_index), 2)
        request_missions = {
            request.request_id: mission.mission_id
            for mission in snapshot.missions
            for request in mission.requests
        }
        response_mission_ids = tuple(
            request_missions[message.request_id] for message, _ in snapshot.message_index
        )
        self.assertEqual(response_mission_ids, ("MISSION-B", "MISSION-A"))

    def test_outbound_decision_and_return_delays_have_distinct_metrics(self):
        profile = _profile(outbound=2, decision=5, returning=3)
        scenario = _simulation_scenario(
            responses=(_response(),),
            profile=profile,
        )

        snapshot = simulate(scenario, _policy(), run_id="RUN-DELAY")

        request = snapshot.missions[0].requests[0]
        self.assertEqual(snapshot.run.result.confirmation_elapsed_seconds, Decimal("10"))
        self.assertEqual(timing(request, now=10).response_elapsed_seconds, Decimal("10"))
        message, deliveries = snapshot.message_index[0]
        self.assertEqual(message.sent_at, Decimal("7"))
        self.assertEqual(deliveries[0].received_at, Decimal("10"))
        self.assertEqual(deliveries[0].communication_rtt_seconds, Decimal("5"))

    def test_zero_delay_is_valid_and_can_complete_at_run_start(self):
        scenario = _simulation_scenario(
            responses=(_response(),),
            profile=_profile(),
        )

        snapshot = simulate(scenario, _policy(), run_id="RUN-ZERO-DELAY")

        self.assertEqual(snapshot.run.status, "completed")
        self.assertEqual(snapshot.run.finished_at, Decimal("0"))
        self.assertEqual(snapshot.run.result.confirmation_elapsed_seconds, Decimal("0"))
        self.assertEqual(snapshot.missions[0].requests[0].response_received_at, Decimal("0"))

    def test_lost_response_has_no_receipt_and_leaves_demand_unconfirmed(self):
        scenario = _simulation_scenario(
            horizon=5,
            responses=(_response(),),
            profile=_profile(loss=(1,)),
        )

        snapshot = simulate(scenario, _policy(), run_id="RUN-LOST")

        self.assertEqual(snapshot.run.status, "horizon_reached")
        self.assertEqual(snapshot.run.result.completed, False)
        self.assertEqual(snapshot.missions[0].requests[0].outcome, "pending")
        message, deliveries = snapshot.message_index[0]
        self.assertEqual(message.request_id, snapshot.missions[0].requests[0].request_id)
        self.assertEqual(len(deliveries), 1)
        self.assertEqual(deliveries[0].disposition, "lost")
        self.assertIsNone(deliveries[0].received_at)

    def test_duplicate_delivery_reuses_message_with_distinct_delivery_ids(self):
        scenario = _simulation_scenario(
            responses=(_response(),),
            profile=_profile(duplicate=(1,)),
        )

        snapshot = simulate(scenario, _policy(), run_id="RUN-DUPLICATE")

        self.assertEqual(snapshot.run.result.confirmed_seats, 1)
        self.assertEqual(len(snapshot.message_index), 1)
        message, deliveries = snapshot.message_index[0]
        self.assertEqual(message.request_id, snapshot.missions[0].requests[0].request_id)
        self.assertEqual(len(deliveries), 2)
        self.assertEqual({delivery.attempt_number for delivery in deliveries}, {1, 2})
        self.assertEqual(len({delivery.delivery_id for delivery in deliveries}), 2)
        self.assertEqual({delivery.disposition for delivery in deliveries}, {"applied", "ignored"})
        self.assertEqual(len(snapshot.missions[0].history), 2)

    def test_reordered_conflicting_and_unknown_responses_are_diagnostic(self):
        central, request = _central_with_pending_request()

        applied = central.record_response(
            RecordResponse(
                message_id="MESSAGE-ARRIVES-FIRST",
                delivery_id="DELIVERY-ARRIVES-FIRST",
                attempt_number=1,
                request_id=request.request_id,
                outcome="accepted",
                confirmed_seats=1,
                sent_at=4,
                received_at=5,
            )
        )
        reordered = central.record_response(
            RecordResponse(
                message_id="MESSAGE-SENT-FIRST",
                delivery_id="DELIVERY-SENT-FIRST",
                attempt_number=1,
                request_id=request.request_id,
                outcome="refused",
                confirmed_seats=0,
                sent_at=1,
                received_at=6,
            )
        )
        unknown = central.record_response(
            RecordResponse(
                message_id="MESSAGE-UNKNOWN",
                delivery_id="DELIVERY-UNKNOWN",
                attempt_number=1,
                request_id="MISSING-REQUEST",
                outcome="accepted",
                confirmed_seats=1,
                sent_at=1,
                received_at=7,
            )
        )

        self.assertEqual(applied.status, "applied")
        self.assertEqual(reordered.status, "ignored")
        self.assertEqual(reordered.reason, "closed_request")
        self.assertEqual(unknown.status, "ignored")
        self.assertEqual(unknown.reason, "unknown_request")
        self.assertEqual(central.get_progress("MISSION-COMM", 7).value.confirmed, 1)
        self.assertEqual(len(central.get_history("MISSION-COMM").value), 2)
        self.assertEqual(
            central.get_deliveries("MESSAGE-SENT-FIRST").value[0].disposition,
            "ignored",
        )
        self.assertEqual(
            central.get_deliveries("MESSAGE-UNKNOWN").value[0].reason,
            "unknown_request",
        )

    def test_response_after_cancellation_is_recorded_without_reopening_request(self):
        central, request = _central_with_pending_request()
        cancelled = central.cancel_request(
            CancelRequest(
                mission_id="MISSION-COMM",
                request_id=request.request_id,
                now=2,
                reason="mission no longer needs this request",
            )
        )

        delivery = central.record_response(
            RecordResponse(
                message_id="MESSAGE-AFTER-CANCEL",
                delivery_id="DELIVERY-AFTER-CANCEL",
                attempt_number=1,
                request_id=request.request_id,
                outcome="accepted",
                confirmed_seats=1,
                sent_at=3,
                received_at=4,
            )
        )

        self.assertEqual(cancelled.status, "applied")
        self.assertEqual(delivery.status, "ignored")
        self.assertEqual(delivery.reason, "closed_request")
        self.assertEqual(central.get_progress("MISSION-COMM", 4).value.confirmed, 0)
        self.assertEqual(central.get_progress("MISSION-COMM", 4).value.pending, 0)
        self.assertEqual(len(central.get_history("MISSION-COMM").value), 2)

    def test_expiration_precedes_response_received_at_the_deadline(self):
        scenario = _simulation_scenario(
            horizon=20,
            pending=True,
            deadline=10,
            responses=(_response(),),
            profile=_profile(outbound=2, decision=5, returning=3),
        )

        snapshot = simulate(scenario, _policy(), run_id="RUN-DEADLINE-TIE")

        first_request = snapshot.missions[0].requests[0]
        self.assertEqual(first_request.outcome, "expired")
        self.assertEqual(first_request.confirmed_seats, 0)
        message, deliveries = snapshot.message_index[0]
        self.assertEqual(message.sent_at, Decimal("7"))
        self.assertEqual(deliveries[0].received_at, Decimal("10"))
        self.assertEqual(deliveries[0].disposition, "late")
        self.assertEqual(deliveries[0].reason, "deadline_expired")
        self.assertEqual(snapshot.run.result.confirmed_seats, 0)


if __name__ == "__main__":
    unittest.main()
