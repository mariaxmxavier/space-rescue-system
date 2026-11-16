"""Deterministic tests for pure mobilisation policy selection."""

from copy import deepcopy
import unittest

from rescue.market.models import (
    B3Market,
    RFQOffer,
    SeatRFQ,
    Ship,
    ShipAvailability,
    ShipOffer,
    ShipOfferRevision,
)
from rescue.market.rules import publish_offer_revision
from rescue.mission.models import Mission, SeatRequest
from rescue.mission.rules import progress
from rescue.mobilisation.models import Candidate, DecisionContext, MobilisationPolicy
from rescue.mobilisation.policies import select_offers


def mission(demand=10, *, pending=0, confirmed=0):
    requests = []
    if pending:
        requests.append(
            SeatRequest(
                request_id="pending-request",
                command_id="pending-command",
                mission_id="mission-1",
                ship_id="already-requested-ship",
                requested_seats=pending,
                confirmed_seats=0,
                outcome="pending",
                submitted_at=1,
                revision_id="pending-revision",
            )
        )
    if confirmed:
        requests.append(
            SeatRequest(
                request_id="confirmed-request",
                command_id="confirmed-command",
                mission_id="mission-1",
                ship_id="already-confirmed-ship",
                requested_seats=confirmed,
                confirmed_seats=confirmed,
                outcome="accepted",
                submitted_at=1,
                response_received_at=2,
                revision_id="confirmed-revision",
            )
        )
    return Mission(
        mission_id="mission-1",
        station_name="Station One",
        people_count=demand,
        created_at=0,
        requests=tuple(requests),
    )


def revision(
    revision_id,
    *,
    revision_number=1,
    capacity=10,
    arrival=0,
    recorded_at=0,
    available=True,
):
    return ShipOfferRevision(
        revision_id=revision_id,
        revision_number=revision_number,
        capacity=capacity,
        arrival_estimate_seconds=arrival,
        available=available,
        recorded_at=recorded_at,
    )


def candidate(
    ship_id,
    revision_value,
    *,
    free_seats=10,
    quote=None,
):
    return Candidate(
        revision=revision_value,
        free_seats=free_seats,
        quote=quote,
        ship_id=ship_id,
    )


def policy(strategy):
    return MobilisationPolicy(
        policy_id=f"policy-{strategy}",
        revision=1,
        name=strategy.replace("_", " ").title(),
        selection_criteria=strategy,
    )


def context(candidate_count, *, decision_id="decision-1", recorded_at=0):
    return DecisionContext(
        decision_id=decision_id,
        recorded_at=recorded_at,
        evaluation_ids=tuple(
            f"evaluation-{index}" for index in range(1, candidate_count + 1)
        ),
    )


class MobilisationPolicyTests(unittest.TestCase):
    def test_earliest_arrival_sorts_absolute_arrival_then_ship_id(self):
        mission_value = mission(demand=6)
        # B arrives at 10 + 5 = 15; A arrives at 0 + 20 = 20.
        later_recorded_earlier_arrival = candidate(
            "B", revision("revision-B", arrival=5, recorded_at=10), free_seats=3
        )
        earlier_recorded_later_arrival = candidate(
            "A", revision("revision-A", arrival=20, recorded_at=0), free_seats=3
        )

        decision = select_offers(
            mission_value,
            (earlier_recorded_later_arrival, later_recorded_earlier_arrival),
            policy("earliest_arrival"),
            context(2),
        )

        self.assertEqual(
            [evaluation.revision.revision_id for evaluation in decision.evaluations],
            ["revision-B", "revision-A"],
        )

        tied_candidates = (
            candidate("B", revision("revision-tie-B", arrival=7, recorded_at=8)),
            candidate("A", revision("revision-tie-A", arrival=10, recorded_at=5)),
        )
        tied_decision = select_offers(
            mission_value,
            tied_candidates,
            policy("earliest_arrival"),
            context(2, decision_id="decision-tie"),
        )
        self.assertEqual(
            [evaluation.revision.revision_id for evaluation in tied_decision.evaluations],
            ["revision-tie-A", "revision-tie-B"],
        )

    def test_largest_capacity_sorts_free_seats_then_arrival_then_ship_id(self):
        mission_value = mission(demand=10)
        candidates = (
            candidate("A", revision("revision-four", arrival=0), free_seats=4),
            candidate("B", revision("revision-six", arrival=20), free_seats=6),
        )

        decision = select_offers(
            mission_value,
            candidates,
            policy("largest_capacity"),
            context(2),
        )

        self.assertEqual(
            [evaluation.revision.revision_id for evaluation in decision.evaluations],
            ["revision-six", "revision-four"],
        )
        self.assertEqual(
            [evaluation.proposed_seats for evaluation in decision.evaluations], [6, 4]
        )
        self.assertTrue(all(evaluation.selected for evaluation in decision.evaluations))

        tied_candidates = (
            candidate("C", revision("revision-tie-C", arrival=10), free_seats=6),
            candidate("B", revision("revision-tie-B", arrival=5), free_seats=6),
            candidate("A", revision("revision-tie-A", arrival=5), free_seats=6),
        )
        tied_decision = select_offers(
            mission(demand=18),
            tied_candidates,
            policy("largest_capacity"),
            context(3, decision_id="decision-tie"),
        )
        self.assertEqual(
            [evaluation.revision.revision_id for evaluation in tied_decision.evaluations],
            ["revision-tie-A", "revision-tie-B", "revision-tie-C"],
        )

    def test_selected_quantity_never_exceeds_additional_needed(self):
        mission_value = mission(demand=10, pending=3)
        available_demand = progress(mission_value).additional_needed
        candidates = (
            candidate("A", revision("revision-A", arrival=1), free_seats=10),
            candidate("B", revision("revision-B", arrival=2), free_seats=5),
        )

        decision = select_offers(
            mission_value,
            candidates,
            policy("earliest_arrival"),
            context(2),
        )

        selected_quantity = sum(
            evaluation.proposed_seats
            for evaluation in decision.evaluations
            if evaluation.selected
        )
        self.assertEqual(available_demand, 7)
        self.assertEqual(selected_quantity, 7)
        self.assertLessEqual(selected_quantity, available_demand)

    def test_unavailable_and_exhausted_candidates_are_explained_as_skipped(self):
        candidates = (
            candidate(
                "offline",
                revision("revision-offline", available=False),
                free_seats=5,
            ),
            candidate("empty", revision("revision-empty"), free_seats=0),
        )

        decision = select_offers(
            mission(demand=5),
            candidates,
            policy("largest_capacity"),
            context(2),
        )

        self.assertEqual(len(decision.evaluations), 2)
        self.assertTrue(all(not evaluation.selected for evaluation in decision.evaluations))
        self.assertTrue(all(evaluation.reason for evaluation in decision.evaluations))
        by_ship = {evaluation.ship_id: evaluation for evaluation in decision.evaluations}
        self.assertEqual(by_ship["offline"].reason, "unavailable")
        self.assertEqual(by_ship["empty"].reason, "exhausted")
        self.assertEqual(
            [evaluation.rank for evaluation in decision.evaluations], [1, 2]
        )

    def test_oversized_quote_is_skipped_as_a_whole_and_revision_basis_is_kept(self):
        oversized_quote = RFQOffer(
            offer_id="quote-oversized",
            rfq_id="rfq-oversized",
            offered_seats=6,
            arrival_estimate_seconds=1,
            expires_at=20,
            recorded_at=1,
        )
        quote_revision = revision("revision-quote", capacity=6, arrival=1)
        whole_quote_candidate = candidate(
            "quote-ship", quote_revision, free_seats=6, quote=oversized_quote
        )
        ordinary_revision = revision("revision-ordinary", capacity=5, arrival=2)
        ordinary_candidate = candidate("ordinary-ship", ordinary_revision, free_seats=5)

        decision = select_offers(
            mission(demand=5),
            (whole_quote_candidate, ordinary_candidate),
            policy("earliest_arrival"),
            context(2),
        )

        by_revision = {
            evaluation.revision.revision_id: evaluation
            for evaluation in decision.evaluations
        }
        oversized_evaluation = by_revision["revision-quote"]
        ordinary_evaluation = by_revision["revision-ordinary"]
        self.assertFalse(oversized_evaluation.selected)
        self.assertEqual(
            oversized_evaluation.reason, "quote_exceeds_remaining_demand"
        )
        self.assertTrue(ordinary_evaluation.selected)
        self.assertIsNone(ordinary_evaluation.reason)
        self.assertEqual(ordinary_evaluation.proposed_seats, 5)
        self.assertEqual(
            sum(
                evaluation.proposed_seats
                for evaluation in decision.evaluations
                if evaluation.selected
            ),
            5,
        )
        self.assertEqual(oversized_evaluation.revision, quote_revision)
        self.assertEqual(ordinary_evaluation.revision, ordinary_revision)

    def test_decision_keeps_its_revision_basis_after_newer_offer_publication(self):
        original = revision("revision-original", revision_number=1, capacity=4)
        newer = revision("revision-newer", revision_number=2, capacity=8, recorded_at=1)
        market = B3Market(
            market_id="market-revisions",
            offers=(
                ShipOffer(
                    offer_id="offer-1",
                    mission_id="mission-1",
                    ship_id="ship-1",
                    revisions=(original,),
                ),
            ),
        )

        revised_market = publish_offer_revision(market, "offer-1", newer)
        decision = select_offers(
            mission(demand=6),
            (candidate("ship-1", original, free_seats=4),),
            policy("earliest_arrival"),
            context(1),
        )

        self.assertEqual(revised_market.offers[0].current_revision, newer)
        self.assertEqual(market.offers[0].current_revision, original)
        self.assertEqual(decision.evaluations[0].revision, original)
        self.assertEqual(decision.evaluations[0].proposed_seats, 4)

    def test_selection_does_not_mutate_mission_candidates_or_market_snapshot(self):
        offer_revision = revision("revision-market", capacity=4, arrival=3)
        ship = Ship(ship_id="ship-1", name="Rescue One")
        availability = ShipAvailability(
            availability_id="availability-1",
            ship_id="ship-1",
            total_seats=4,
            arrival_estimate_seconds=3,
            available=True,
            recorded_at=1,
        )
        rfq = SeatRFQ(
            rfq_id="rfq-1",
            mission_id="mission-1",
            ship_id="ship-1",
            availability_id="availability-1",
            requested_seats=4,
            status="quoted",
            sent_at=1,
        )
        quote = RFQOffer(
            offer_id="quote-1",
            rfq_id="rfq-1",
            offered_seats=4,
            arrival_estimate_seconds=3,
            expires_at=10,
            recorded_at=2,
        )
        market = B3Market(
            market_id="market-1",
            ships=(ship,),
            availabilities=(availability,),
            rfqs=(rfq,),
            quotes=(quote,),
            offers=(
                ShipOffer(
                    offer_id="offer-1",
                    mission_id="mission-1",
                    ship_id="ship-1",
                    revisions=(offer_revision,),
                ),
            ),
        )
        candidates = (candidate("ship-1", offer_revision, free_seats=4, quote=quote),)
        mission_value = mission(demand=4)
        market_before = deepcopy(market)
        candidates_before = deepcopy(candidates)
        mission_before = deepcopy(mission_value)

        decision = select_offers(
            mission_value,
            candidates,
            policy("largest_capacity"),
            context(1),
        )

        self.assertEqual(market, market_before)
        self.assertEqual(candidates, candidates_before)
        self.assertEqual(mission_value, mission_before)
        self.assertEqual(decision.evaluations[0].revision, offer_revision)


if __name__ == "__main__":
    unittest.main()
