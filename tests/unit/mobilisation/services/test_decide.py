"""Decision service tests: allocator validation, reasons, identity, trace logging."""

from __future__ import annotations

import logging
from copy import deepcopy
from dataclasses import replace

import pytest

from rescue.market.models import (
    B3Market,
    RFQOffer,
    SeatRFQ,
    Ship,
    ShipAvailability,
    ShipOffer,
)
from rescue.market.rules import publish_offer_revision
from rescue.mobilisation.algorithms import ALLOCATORS
from rescue.mobilisation.models.algorithm_name import AlgorithmName
from rescue.mobilisation.models.allocation import Allocation, AllocationResult
from rescue.mobilisation.models.trace_step import TraceStep
from rescue.mobilisation.services.decide import select_offers
from rescue.values import DomainValidationError

ALGORITHM = AlgorithmName.EARLIEST_ARRIVAL


def allocator_of(seats_by_ship, *, trace=None, seen=None):
    """Build an injected allocator that returns fixed seats in the given order."""

    def allocate(candidates, demand, at):
        if seen is not None:
            seen.append((candidates, demand, at))
        steps = (
            trace
            if trace is not None
            else (TraceStep(algorithm=ALGORITHM, step="result", ship_id=None, detail=()),)
        )
        return AllocationResult(
            algorithm=ALGORITHM,
            allocations=tuple(Allocation(ship_id=s, seats=n) for s, n in seats_by_ship),
            trace=tuple(steps),
        )

    return allocate


def decide(mission, candidates, policy, context, seats_by_ship, **kwargs):
    return select_offers(
        mission,
        candidates,
        policy,
        context,
        allocators={ALGORITHM: allocator_of(seats_by_ship, **kwargs)},
    )


@pytest.fixture
def two_ships(candidate_factory, revision_factory):
    return (
        candidate_factory("A", revision_factory("rev-A", capacity=5), free_seats=5),
        candidate_factory("B", revision_factory("rev-B", capacity=5), free_seats=5),
    )


@pytest.fixture
def static_skips(candidate_factory, revision_factory, quote_factory):
    return {
        "unavailable": candidate_factory("S", revision_factory("rev-S", available=False)),
        "quote_not_held": candidate_factory(
            "S", revision_factory("rev-S"), quote=quote_factory("q", 2, status="rejected")
        ),
        "expired_quote": candidate_factory(
            "S", revision_factory("rev-S"), quote=quote_factory("q", 2, expires_at=5)
        ),
    }


def test_valid_injected_allocator_produces_decision_in_allocation_order(
    mission_factory, two_ships, policy_factory, decision_context_factory
):
    decision = decide(
        mission_factory(6),
        two_ships,
        policy_factory(),
        decision_context_factory(2),
        [("B", 4), ("A", 2)],
    )

    assert [
        (e.ship_id, e.evaluation_id, e.rank, e.proposed_seats, e.selected, e.reason)
        for e in decision.evaluations
    ] == [
        ("B", "evaluation-1", 1, 4, True, None),
        ("A", "evaluation-2", 2, 2, True, None),
    ]
    assert decision.remaining_demand == 0
    assert decision.decision_id == "decision-1"
    assert decision.mission_id == "mission-1"
    assert decision.policy_id == "policy-earliest_arrival"
    assert decision.policy_revision == 1


def test_remaining_demand_is_demand_minus_allocated_seats(
    mission_factory, two_ships, policy_factory, decision_context_factory
):
    decision = decide(
        mission_factory(10, pending=1),
        two_ships,
        policy_factory(),
        decision_context_factory(2),
        [("A", 3), ("B", 0)],
    )

    assert decision.remaining_demand == 6


def test_allocator_receives_unmet_demand_and_decision_time(
    mission_factory, two_ships, policy_factory, decision_context_factory
):
    seen = []

    decide(
        mission_factory(10, pending=3),
        two_ships,
        policy_factory(),
        decision_context_factory(2, recorded_at=9),
        [("A", 0), ("B", 0)],
        seen=seen,
    )

    assert len(seen) == 1
    candidates, demand, at = seen[0]
    assert {c.ship_id for c in candidates} == {"A", "B"}
    assert (demand, at) == (7, 9)


def test_evaluations_carry_revision_and_quote_of_their_candidate(
    mission_factory,
    candidate_factory,
    revision_factory,
    quote_factory,
    policy_factory,
    decision_context_factory,
):
    held = quote_factory("q", 3)
    revision = revision_factory("rev-Q", capacity=5)
    candidate = candidate_factory("Q", revision, free_seats=5, quote=held)

    decision = decide(
        mission_factory(5),
        (candidate,),
        policy_factory(),
        decision_context_factory(1),
        [("Q", 3)],
    )

    assert decision.evaluations[0].revision == revision
    assert decision.evaluations[0].quote == held


def test_held_quote_is_selected_at_its_full_quantity(
    mission_factory,
    candidate_factory,
    revision_factory,
    quote_factory,
    policy_factory,
    decision_context_factory,
):
    candidate = candidate_factory(
        "Q", revision_factory("rev-Q"), free_seats=6, quote=quote_factory("q", 4)
    )

    decision = decide(
        mission_factory(10),
        (candidate,),
        policy_factory(),
        decision_context_factory(1),
        [("Q", 4)],
    )

    assert decision.evaluations[0].proposed_seats == 4
    assert decision.remaining_demand == 6


def test_empty_candidates_leave_demand_unchanged(
    mission_factory, policy_factory, decision_context_factory
):
    decision = decide(
        mission_factory(7, pending=2, confirmed=1),
        (),
        policy_factory(),
        decision_context_factory(0),
        [],
    )

    assert decision.evaluations == ()
    assert decision.remaining_demand == 4


def test_duplicate_candidate_in_allocation_is_rejected(
    mission_factory, two_ships, policy_factory, decision_context_factory
):
    with pytest.raises(DomainValidationError):
        decide(
            mission_factory(6),
            two_ships,
            policy_factory(),
            decision_context_factory(2),
            [("A", 1), ("A", 1)],
        )


def test_missing_candidate_in_allocation_is_rejected(
    mission_factory, two_ships, policy_factory, decision_context_factory
):
    with pytest.raises(DomainValidationError):
        decide(
            mission_factory(6),
            two_ships,
            policy_factory(),
            decision_context_factory(2),
            [("A", 1)],
        )


def test_foreign_candidate_in_allocation_is_rejected(
    mission_factory, two_ships, policy_factory, decision_context_factory
):
    with pytest.raises(DomainValidationError):
        decide(
            mission_factory(6),
            two_ships,
            policy_factory(),
            decision_context_factory(2),
            [("A", 1), ("Z", 1)],
        )


def test_extra_foreign_candidate_alongside_all_inputs_is_rejected(
    mission_factory, two_ships, policy_factory, decision_context_factory
):
    with pytest.raises(DomainValidationError):
        decide(
            mission_factory(6),
            two_ships,
            policy_factory(),
            decision_context_factory(2),
            [("A", 1), ("B", 1), ("Z", 1)],
        )


def test_negative_seats_are_rejected(
    mission_factory, two_ships, policy_factory, decision_context_factory
):
    with pytest.raises(DomainValidationError):
        decide(
            mission_factory(6),
            two_ships,
            policy_factory(),
            decision_context_factory(2),
            [("A", -1), ("B", 0)],
        )


def test_seats_above_allocatable_are_rejected(
    mission_factory,
    candidate_factory,
    revision_factory,
    policy_factory,
    decision_context_factory,
):
    small = candidate_factory("A", revision_factory("rev-A", capacity=5), free_seats=2)

    with pytest.raises(DomainValidationError):
        decide(
            mission_factory(6),
            (small,),
            policy_factory(),
            decision_context_factory(1),
            [("A", 3)],
        )


def test_seats_above_capacity_cap_even_when_free_seats_are_larger(
    mission_factory,
    candidate_factory,
    revision_factory,
    policy_factory,
    decision_context_factory,
):
    capped = candidate_factory("A", revision_factory("rev-A", capacity=2), free_seats=9)

    with pytest.raises(DomainValidationError):
        decide(
            mission_factory(6),
            (capped,),
            policy_factory(),
            decision_context_factory(1),
            [("A", 3)],
        )


def test_total_seats_above_demand_are_rejected(
    mission_factory, two_ships, policy_factory, decision_context_factory
):
    with pytest.raises(DomainValidationError):
        decide(
            mission_factory(6),
            two_ships,
            policy_factory(),
            decision_context_factory(2),
            [("A", 4), ("B", 3)],
        )


def test_seats_when_demand_is_zero_are_rejected(
    mission_factory, two_ships, policy_factory, decision_context_factory
):
    with pytest.raises(DomainValidationError):
        decide(
            mission_factory(10, pending=6, confirmed=4),
            two_ships,
            policy_factory(),
            decision_context_factory(2),
            [("A", 1), ("B", 0)],
        )


@pytest.mark.parametrize("seats", [1, 2, 4])
def test_split_quote_seats_are_rejected(
    seats,
    mission_factory,
    candidate_factory,
    revision_factory,
    quote_factory,
    policy_factory,
    decision_context_factory,
):
    candidate = candidate_factory(
        "Q", revision_factory("rev-Q"), free_seats=6, quote=quote_factory("q", 3)
    )

    with pytest.raises(DomainValidationError):
        decide(
            mission_factory(10),
            (candidate,),
            policy_factory(),
            decision_context_factory(1),
            [("Q", seats)],
        )


def test_quote_seats_of_zero_are_accepted(
    mission_factory,
    candidate_factory,
    revision_factory,
    quote_factory,
    policy_factory,
    decision_context_factory,
):
    candidate = candidate_factory(
        "Q", revision_factory("rev-Q"), free_seats=6, quote=quote_factory("q", 3)
    )

    decision = decide(
        mission_factory(10),
        (candidate,),
        policy_factory(),
        decision_context_factory(1),
        [("Q", 0)],
    )

    assert decision.evaluations[0].reason == "not_chosen"


@pytest.mark.parametrize("case", ["unavailable", "quote_not_held", "expired_quote"])
def test_seats_given_to_a_static_skip_are_rejected(
    case, static_skips, mission_factory, policy_factory, decision_context_factory
):
    with pytest.raises(DomainValidationError):
        decide(
            mission_factory(10),
            (static_skips[case],),
            policy_factory(),
            decision_context_factory(1, recorded_at=5),
            [("S", 2)],
        )


@pytest.mark.parametrize("case", ["unavailable", "quote_not_held", "expired_quote"])
def test_static_skip_reasons_are_reported(
    case, static_skips, mission_factory, policy_factory, decision_context_factory
):
    decision = decide(
        mission_factory(10),
        (static_skips[case],),
        policy_factory(),
        decision_context_factory(1, recorded_at=5),
        [("S", 0)],
    )

    evaluation = decision.evaluations[0]
    assert (evaluation.selected, evaluation.proposed_seats, evaluation.reason) == (
        False,
        0,
        case,
    )


def test_static_reason_wins_over_insufficient_demand(
    mission_factory, candidate_factory, revision_factory, policy_factory, decision_context_factory
):
    candidate = candidate_factory("S", revision_factory("rev-S", available=False))

    decision = decide(
        mission_factory(10, pending=6, confirmed=4),
        (candidate,),
        policy_factory(),
        decision_context_factory(1),
        [("S", 0)],
    )

    assert decision.evaluations[0].reason == "unavailable"


def test_insufficient_demand_wins_over_exhausted(
    mission_factory, candidate_factory, revision_factory, policy_factory, decision_context_factory
):
    candidate = candidate_factory("E", revision_factory("rev-E"), free_seats=0)

    decision = decide(
        mission_factory(10, pending=6, confirmed=4),
        (candidate,),
        policy_factory(),
        decision_context_factory(1),
        [("E", 0)],
    )

    assert decision.evaluations[0].reason == "insufficient_demand"


def test_exhausted_wins_over_quote_reasons(
    mission_factory,
    candidate_factory,
    revision_factory,
    quote_factory,
    policy_factory,
    decision_context_factory,
):
    candidate = candidate_factory(
        "E", revision_factory("rev-E"), free_seats=0, quote=quote_factory("q", 6)
    )

    decision = decide(
        mission_factory(5),
        (candidate,),
        policy_factory(),
        decision_context_factory(1),
        [("E", 0)],
    )

    assert decision.evaluations[0].reason == "exhausted"


def test_quote_exceeds_remaining_demand_wins_over_insufficient_capacity(
    mission_factory,
    candidate_factory,
    revision_factory,
    quote_factory,
    policy_factory,
    decision_context_factory,
):
    candidate = candidate_factory(
        "Q", revision_factory("rev-Q", capacity=4), free_seats=4, quote=quote_factory("q", 6)
    )

    decision = decide(
        mission_factory(5),
        (candidate,),
        policy_factory(),
        decision_context_factory(1),
        [("Q", 0)],
    )

    assert decision.evaluations[0].reason == "quote_exceeds_remaining_demand"


def test_insufficient_capacity_wins_over_not_chosen(
    mission_factory,
    candidate_factory,
    revision_factory,
    quote_factory,
    policy_factory,
    decision_context_factory,
):
    candidate = candidate_factory(
        "Q", revision_factory("rev-Q", capacity=4), free_seats=4, quote=quote_factory("q", 6)
    )

    decision = decide(
        mission_factory(10),
        (candidate,),
        policy_factory(),
        decision_context_factory(1),
        [("Q", 0)],
    )

    assert decision.evaluations[0].reason == "insufficient_capacity"


def test_zero_seat_candidate_with_remaining_demand_is_not_chosen(
    mission_factory, two_ships, policy_factory, decision_context_factory
):
    decision = decide(
        mission_factory(5),
        two_ships,
        policy_factory(),
        decision_context_factory(2),
        [("A", 2), ("B", 0)],
    )

    assert decision.evaluations[1].reason == "not_chosen"
    assert decision.evaluations[1].selected is False


def test_demand_consumed_earlier_in_rank_order_gives_insufficient_demand_later(
    mission_factory, two_ships, policy_factory, decision_context_factory
):
    decision = decide(
        mission_factory(5),
        two_ships,
        policy_factory(),
        decision_context_factory(2),
        [("A", 5), ("B", 0)],
    )

    assert [(e.ship_id, e.reason) for e in decision.evaluations] == [
        ("A", None),
        ("B", "insufficient_demand"),
    ]


def test_ranks_follow_allocation_order_not_input_order(
    mission_factory, two_ships, policy_factory, decision_context_factory
):
    decision = decide(
        mission_factory(4),
        two_ships,
        policy_factory(),
        decision_context_factory(2),
        [("B", 2), ("A", 2)],
    )

    assert [(e.ship_id, e.rank, e.evaluation_id) for e in decision.evaluations] == [
        ("B", 1, "evaluation-1"),
        ("A", 2, "evaluation-2"),
    ]


def test_non_mission_is_rejected(two_ships, policy_factory, decision_context_factory):
    with pytest.raises(DomainValidationError, match="Mission"):
        select_offers(object(), two_ships, policy_factory(), decision_context_factory(2))


def test_non_policy_is_rejected(mission_factory, two_ships, decision_context_factory):
    with pytest.raises(DomainValidationError, match="MobilisationPolicy"):
        select_offers(mission_factory(5), two_ships, object(), decision_context_factory(2))


def test_non_context_is_rejected(mission_factory, two_ships, policy_factory):
    with pytest.raises(DomainValidationError, match="DecisionContext"):
        select_offers(mission_factory(5), two_ships, policy_factory(), object())


def test_non_candidate_items_are_rejected(
    mission_factory, policy_factory, decision_context_factory
):
    with pytest.raises(DomainValidationError, match="Candidate"):
        select_offers(mission_factory(5), ("ship",), policy_factory(), decision_context_factory(1))


def test_evaluation_id_count_must_match_candidates(
    mission_factory, two_ships, policy_factory, decision_context_factory
):
    with pytest.raises(DomainValidationError, match="evaluation ID"):
        select_offers(mission_factory(5), two_ships, policy_factory(), decision_context_factory(1))


def test_duplicate_ship_candidates_are_rejected(
    mission_factory, candidate_factory, revision_factory, policy_factory, decision_context_factory
):
    twins = (
        candidate_factory("A", revision_factory("rev-1")),
        candidate_factory("A", revision_factory("rev-2")),
    )

    with pytest.raises(DomainValidationError, match="one offer per ship"):
        select_offers(mission_factory(5), twins, policy_factory(), decision_context_factory(2))


def test_strategy_without_a_registered_allocator_is_rejected(
    mission_factory, two_ships, policy_factory, decision_context_factory
):
    with pytest.raises(DomainValidationError):
        select_offers(
            mission_factory(5),
            two_ships,
            policy_factory("unknown_strategy"),
            decision_context_factory(2),
            allocators={ALGORITHM: allocator_of([])},
        )


def test_strategy_selects_the_allocator_registered_for_it(
    mission_factory, two_ships, policy_factory, decision_context_factory
):
    seen = []
    idle = [("A", 0), ("B", 0)]

    select_offers(
        mission_factory(5),
        two_ships,
        policy_factory("largest_capacity"),
        decision_context_factory(2),
        allocators={
            AlgorithmName.EARLIEST_ARRIVAL: allocator_of(idle),
            AlgorithmName.LARGEST_CAPACITY: allocator_of(idle, seen=seen),
        },
    )

    assert len(seen) == 1


def test_default_allocators_are_used_when_none_are_passed(
    mission_factory,
    candidate_factory,
    revision_factory,
    policy_factory,
    decision_context_factory,
):
    candidates = (
        candidate_factory("C", revision_factory("revision-C", arrival=3), free_seats=5),
        candidate_factory("A", revision_factory("revision-A", arrival=1), free_seats=4),
        candidate_factory("B", revision_factory("revision-B", arrival=2), free_seats=6),
    )

    decision = select_offers(
        mission_factory(12, pending=2, confirmed=3),
        candidates,
        policy_factory(),
        decision_context_factory(3),
    )

    assert AlgorithmName.EARLIEST_ARRIVAL in ALLOCATORS
    assert [
        (e.ship_id, e.evaluation_id, e.rank, e.proposed_seats, e.reason)
        for e in decision.evaluations
    ] == [
        ("A", "evaluation-1", 1, 4, None),
        ("B", "evaluation-2", 2, 3, None),
        ("C", "evaluation-3", 3, 0, "insufficient_demand"),
    ]
    assert decision.remaining_demand == 0


def test_default_largest_capacity_orders_by_free_seats(
    mission_factory,
    candidate_factory,
    revision_factory,
    policy_factory,
    decision_context_factory,
):
    candidates = (
        candidate_factory("A", revision_factory("revision-four", arrival=0), free_seats=4),
        candidate_factory("B", revision_factory("revision-six", arrival=20), free_seats=6),
    )

    decision = select_offers(
        mission_factory(10),
        candidates,
        policy_factory("largest_capacity"),
        decision_context_factory(2),
    )

    assert [(e.ship_id, e.proposed_seats) for e in decision.evaluations] == [("B", 6), ("A", 4)]


def test_default_oversized_quote_is_skipped_and_ordinary_ship_covers_demand(
    mission_factory,
    candidate_factory,
    revision_factory,
    quote_factory,
    policy_factory,
    decision_context_factory,
):
    candidates = (
        candidate_factory(
            "quote-ship",
            revision_factory("revision-quote", capacity=6, arrival=1),
            free_seats=6,
            quote=quote_factory("quote-oversized", 6),
        ),
        candidate_factory(
            "ordinary-ship",
            revision_factory("revision-ordinary", capacity=5, arrival=2),
            free_seats=5,
        ),
    )

    decision = select_offers(
        mission_factory(5), candidates, policy_factory(), decision_context_factory(2)
    )

    assert [(e.ship_id, e.proposed_seats, e.reason) for e in decision.evaluations] == [
        ("quote-ship", 0, "quote_exceeds_remaining_demand"),
        ("ordinary-ship", 5, None),
    ]


def test_trace_steps_are_logged_at_debug_with_step_fields(
    caplog, mission_factory, two_ships, policy_factory, decision_context_factory
):
    trace = (
        TraceStep(algorithm=ALGORITHM, step="consider", ship_id="A", detail=(("seats", "2"),)),
        TraceStep(algorithm=ALGORITHM, step="pick", ship_id="B", detail=()),
        TraceStep(algorithm=ALGORITHM, step="result", ship_id=None, detail=()),
    )

    with caplog.at_level(logging.DEBUG, logger="rescue.mobilisation"):
        decide(
            mission_factory(6),
            two_ships,
            policy_factory(),
            decision_context_factory(2),
            [("A", 2), ("B", 0)],
            trace=trace,
        )

    records = [r for r in caplog.records if r.name == "rescue.mobilisation"]
    assert [r.levelno for r in records] == [logging.DEBUG] * 3
    assert [(r.step, r.ship_id, r.algorithm) for r in records] == [
        ("consider", "A", ALGORITHM),
        ("pick", "B", ALGORITHM),
        ("result", None, ALGORITHM),
    ]


def test_rejected_allocation_logs_no_trace(
    caplog, mission_factory, two_ships, policy_factory, decision_context_factory
):
    with caplog.at_level(logging.DEBUG, logger="rescue.mobilisation"):
        with pytest.raises(DomainValidationError):
            decide(
                mission_factory(6),
                two_ships,
                policy_factory(),
                decision_context_factory(2),
                [("A", 9), ("B", 0)],
            )

    assert [r for r in caplog.records if r.name == "rescue.mobilisation"] == []


def test_default_earliest_arrival_sorts_absolute_arrival_then_ship_id(
    mission_factory, candidate_factory, revision_factory, policy_factory, decision_context_factory
):
    later_recorded_earlier_arrival = candidate_factory(
        "B", revision_factory("revision-B", arrival=5, recorded_at=10), free_seats=3
    )
    earlier_recorded_later_arrival = candidate_factory(
        "A", revision_factory("revision-A", arrival=20, recorded_at=0), free_seats=3
    )

    decision = select_offers(
        mission_factory(6),
        (earlier_recorded_later_arrival, later_recorded_earlier_arrival),
        policy_factory(),
        decision_context_factory(2),
    )
    tied = select_offers(
        mission_factory(6),
        (
            candidate_factory("B", revision_factory("revision-tie-B", arrival=7, recorded_at=8)),
            candidate_factory("A", revision_factory("revision-tie-A", arrival=10, recorded_at=5)),
        ),
        policy_factory(),
        decision_context_factory(2),
    )

    assert [e.revision.revision_id for e in decision.evaluations] == ["revision-B", "revision-A"]
    assert [e.revision.revision_id for e in tied.evaluations] == [
        "revision-tie-A",
        "revision-tie-B",
    ]


def test_default_largest_capacity_ties_break_on_arrival_then_ship_id(
    mission_factory, candidate_factory, revision_factory, policy_factory, decision_context_factory
):
    candidates = (
        candidate_factory("C", revision_factory("revision-tie-C", arrival=10), free_seats=6),
        candidate_factory("B", revision_factory("revision-tie-B", arrival=5), free_seats=6),
        candidate_factory("A", revision_factory("revision-tie-A", arrival=5), free_seats=6),
    )

    decision = select_offers(
        mission_factory(18),
        candidates,
        policy_factory("largest_capacity"),
        decision_context_factory(3),
    )

    assert [e.revision.revision_id for e in decision.evaluations] == [
        "revision-tie-A",
        "revision-tie-B",
        "revision-tie-C",
    ]
    assert all(e.selected for e in decision.evaluations)


def test_default_selected_quantity_never_exceeds_additional_needed(
    mission_factory, candidate_factory, revision_factory, policy_factory, decision_context_factory
):
    candidates = (
        candidate_factory("A", revision_factory("revision-A", arrival=1), free_seats=10),
        candidate_factory("B", revision_factory("revision-B", arrival=2), free_seats=5),
    )

    decision = select_offers(
        mission_factory(10, pending=3), candidates, policy_factory(), decision_context_factory(2)
    )

    assert sum(e.proposed_seats for e in decision.evaluations if e.selected) == 7
    assert decision.remaining_demand == 0


def test_default_held_quote_is_taken_whole_beside_an_ordinary_ship(
    mission_factory,
    candidate_factory,
    revision_factory,
    quote_factory,
    policy_factory,
    decision_context_factory,
):
    candidates = (
        candidate_factory(
            "quoted",
            revision_factory("revision-quoted", arrival=1),
            free_seats=6,
            quote=quote_factory("quote-held", 4),
        ),
        candidate_factory(
            "ordinary", revision_factory("revision-ordinary", arrival=2), free_seats=6
        ),
    )

    decision = select_offers(
        mission_factory(10), candidates, policy_factory(), decision_context_factory(2)
    )

    assert [(e.ship_id, e.proposed_seats, e.selected, e.reason) for e in decision.evaluations] == [
        ("quoted", 4, True, None),
        ("ordinary", 6, True, None),
    ]
    assert decision.remaining_demand == 0


def test_default_static_skip_precedence_and_zero_demand_are_explicit(
    mission_factory,
    candidate_factory,
    revision_factory,
    quote_factory,
    policy_factory,
    decision_context_factory,
):
    candidates = (
        candidate_factory(
            "unavailable",
            revision_factory("revision-unavailable", available=False),
            quote=quote_factory("quote-unavailable", 2, expires_at=5, status="accepted"),
        ),
        candidate_factory(
            "not-held",
            revision_factory("revision-not-held"),
            quote=quote_factory("quote-not-held", 2, expires_at=5, status="rejected"),
        ),
        candidate_factory(
            "expired",
            revision_factory("revision-expired"),
            quote=quote_factory("quote-expired", 2, expires_at=5),
        ),
        candidate_factory("exhausted", revision_factory("revision-exhausted"), free_seats=0),
    )

    decision = select_offers(
        mission_factory(10, pending=6, confirmed=4),
        candidates,
        policy_factory(),
        decision_context_factory(4, recorded_at=5),
    )

    by_ship = {e.ship_id: e for e in decision.evaluations}
    assert by_ship["unavailable"].reason == "unavailable"
    assert by_ship["not-held"].reason == "quote_not_held"
    assert by_ship["expired"].reason == "expired_quote"
    assert by_ship["exhausted"].reason == "insufficient_demand"
    assert decision.remaining_demand == 0
    assert sum(e.proposed_seats for e in decision.evaluations) == 0


def test_default_held_quote_exceeding_candidate_capacity_is_skipped(
    mission_factory,
    candidate_factory,
    revision_factory,
    quote_factory,
    policy_factory,
    decision_context_factory,
):
    candidate = candidate_factory(
        "ship",
        revision_factory("revision-small", capacity=4),
        free_seats=4,
        quote=quote_factory("quote-capacity", 6),
    )

    decision = select_offers(
        mission_factory(10), (candidate,), policy_factory(), decision_context_factory(1)
    )

    evaluation = decision.evaluations[0]
    assert (evaluation.selected, evaluation.reason, evaluation.proposed_seats) == (
        False,
        "insufficient_capacity",
        0,
    )


def test_default_unavailable_and_exhausted_candidates_are_explained_as_skipped(
    mission_factory, candidate_factory, revision_factory, policy_factory, decision_context_factory
):
    candidates = (
        candidate_factory("offline", revision_factory("revision-offline", available=False)),
        candidate_factory("empty", revision_factory("revision-empty"), free_seats=0),
    )

    decision = select_offers(
        mission_factory(5),
        candidates,
        policy_factory("largest_capacity"),
        decision_context_factory(2),
    )

    by_ship = {e.ship_id: e for e in decision.evaluations}
    assert not any(e.selected for e in decision.evaluations)
    assert by_ship["offline"].reason == "unavailable"
    assert by_ship["empty"].reason == "exhausted"
    assert [e.rank for e in decision.evaluations] == [1, 2]


def test_oversized_quote_keeps_its_revision_basis_while_ordinary_ship_covers_demand(
    mission_factory,
    candidate_factory,
    revision_factory,
    quote_factory,
    policy_factory,
    decision_context_factory,
):
    quote_revision = revision_factory("revision-quote", capacity=6, arrival=1)
    ordinary_revision = revision_factory("revision-ordinary", capacity=5, arrival=2)
    candidates = (
        candidate_factory(
            "quote-ship", quote_revision, free_seats=6, quote=quote_factory("quote-oversized", 6)
        ),
        candidate_factory("ordinary-ship", ordinary_revision, free_seats=5),
    )

    decision = select_offers(
        mission_factory(5), candidates, policy_factory(), decision_context_factory(2)
    )

    by_revision = {e.revision.revision_id: e for e in decision.evaluations}
    assert not by_revision["revision-quote"].selected
    assert by_revision["revision-ordinary"].proposed_seats == 5
    assert by_revision["revision-quote"].revision == quote_revision
    assert by_revision["revision-ordinary"].revision == ordinary_revision


def test_decision_keeps_its_revision_basis_after_newer_offer_publication(
    mission_factory, candidate_factory, revision_factory, policy_factory, decision_context_factory
):
    original = revision_factory("revision-original", capacity=4)
    newer = replace(
        revision_factory("revision-newer", capacity=8, recorded_at=1), revision_number=2
    )
    market = B3Market(
        market_id="market-revisions",
        offers=(
            ShipOffer(
                offer_id="offer-1", mission_id="mission-1", ship_id="ship-1", revisions=(original,)
            ),
        ),
    )

    revised_market = publish_offer_revision(market, "offer-1", newer)
    decision = select_offers(
        mission_factory(6),
        (candidate_factory("ship-1", original, free_seats=4),),
        policy_factory(),
        decision_context_factory(1),
    )

    assert revised_market.offers[0].current_revision == newer
    assert market.offers[0].current_revision == original
    assert decision.evaluations[0].revision == original
    assert decision.evaluations[0].proposed_seats == 4


def test_selection_does_not_mutate_mission_candidates_or_market_snapshot(
    mission_factory, candidate_factory, revision_factory, policy_factory, decision_context_factory
):
    offer_revision = revision_factory("revision-market", capacity=4, arrival=3)
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
        ships=(Ship(ship_id="ship-1", name="Rescue One"),),
        availabilities=(
            ShipAvailability(
                availability_id="availability-1",
                ship_id="ship-1",
                total_seats=4,
                arrival_estimate_seconds=3,
                available=True,
                recorded_at=1,
            ),
        ),
        rfqs=(
            SeatRFQ(
                rfq_id="rfq-1",
                mission_id="mission-1",
                ship_id="ship-1",
                availability_id="availability-1",
                requested_seats=4,
                status="quoted",
                sent_at=1,
            ),
        ),
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
    candidates = (candidate_factory("ship-1", offer_revision, free_seats=4, quote=quote),)
    mission = mission_factory(4)
    snapshots = deepcopy((market, candidates, mission))

    decision = select_offers(
        mission, candidates, policy_factory("largest_capacity"), decision_context_factory(1)
    )

    assert (market, candidates, mission) == snapshots
    assert decision.evaluations[0].revision == offer_revision
