"""Regression tests pinning the greedy allocators to the original selection rules."""

from __future__ import annotations

import pytest

from rescue.mobilisation.algorithms.greedy import (
    allocate_earliest_arrival,
    allocate_largest_capacity,
)
from rescue.mobilisation.services.decide import select_offers


def seats_by_ship(result):
    return [(a.ship_id, a.seats) for a in result.allocations]


def test_earliest_arrival_orders_by_absolute_arrival_then_ship_id(
    candidate_factory, revision_factory
):
    candidates = (
        candidate_factory("C", revision_factory("r-C", arrival=5, recorded_at=10), free_seats=1),
        candidate_factory("B", revision_factory("r-B", arrival=15, recorded_at=0), free_seats=1),
        candidate_factory("A", revision_factory("r-A", arrival=15, recorded_at=0), free_seats=1),
        candidate_factory("D", revision_factory("r-D", arrival=1, recorded_at=0), free_seats=1),
    )

    result = allocate_earliest_arrival(candidates, 4, 0)

    assert [ship for ship, _ in seats_by_ship(result)] == ["D", "A", "B", "C"]


def test_largest_capacity_orders_by_allocatable_then_arrival_then_ship_id(
    candidate_factory, revision_factory
):
    candidates = (
        candidate_factory("C", revision_factory("r-C", arrival=10), free_seats=6),
        candidate_factory("B", revision_factory("r-B", arrival=5), free_seats=6),
        candidate_factory("A", revision_factory("r-A", arrival=5), free_seats=6),
        candidate_factory("Z", revision_factory("r-Z", arrival=0), free_seats=2),
        candidate_factory("Y", revision_factory("r-Y", arrival=99), free_seats=7),
    )

    result = allocate_largest_capacity(candidates, 27, 0)

    assert [ship for ship, _ in seats_by_ship(result)] == ["Y", "A", "B", "C", "Z"]


@pytest.mark.parametrize("allocate", (allocate_earliest_arrival, allocate_largest_capacity))
def test_held_quote_is_taken_whole_or_not_at_all(
    allocate, candidate_factory, revision_factory, quote_factory
):
    fits = candidate_factory(
        "fits", revision_factory("r-fits", capacity=6), free_seats=6, quote=quote_factory("q1", 4)
    )
    too_big_for_demand = candidate_factory(
        "big", revision_factory("r-big", capacity=6), free_seats=6, quote=quote_factory("q2", 6)
    )
    too_big_for_ship = candidate_factory(
        "small", revision_factory("r-small", capacity=3), free_seats=3, quote=quote_factory("q3", 4)
    )

    result = allocate((fits, too_big_for_demand, too_big_for_ship), 5, 0)
    seats = dict(seats_by_ship(result))

    assert seats["fits"] == 4
    assert seats["big"] == 0
    assert seats["small"] == 0


@pytest.mark.parametrize("allocate", (allocate_earliest_arrival, allocate_largest_capacity))
def test_every_static_skip_gets_zero_seats(
    allocate, candidate_factory, revision_factory, quote_factory
):
    candidates = (
        candidate_factory("unavailable", revision_factory("r-u", available=False)),
        candidate_factory(
            "rejected", revision_factory("r-r"), quote=quote_factory("q-r", 2, status="rejected")
        ),
        candidate_factory(
            "expired", revision_factory("r-e"), quote=quote_factory("q-e", 2, expires_at=5)
        ),
        candidate_factory("empty", revision_factory("r-x"), free_seats=0),
    )

    result = allocate(candidates, 10, 5)

    assert sorted(seats_by_ship(result)) == [
        ("empty", 0),
        ("expired", 0),
        ("rejected", 0),
        ("unavailable", 0),
    ]


def test_default_policy_reproduces_the_characterised_decision(
    mission_factory, candidate_factory, revision_factory, policy_factory, decision_context_factory
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

    assert [
        (e.ship_id, e.evaluation_id, e.rank, e.proposed_seats, e.reason)
        for e in decision.evaluations
    ] == [
        ("A", "evaluation-1", 1, 4, None),
        ("B", "evaluation-2", 2, 3, None),
        ("C", "evaluation-3", 3, 0, "insufficient_demand"),
    ]
    assert decision.remaining_demand == 0


def test_default_policy_reproduces_the_characterised_oversized_quote_decision(
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


ALLOCATORS = (allocate_earliest_arrival, allocate_largest_capacity)


def steps_of(result, name):
    return [s for s in result.trace if s.step == name]


@pytest.mark.parametrize("allocate", ALLOCATORS)
def test_trace_names_every_candidate_with_a_pick_or_skip(
    allocate, candidate_factory, revision_factory, quote_factory
):
    candidates = (
        candidate_factory("picked", revision_factory("r-p", arrival=1), free_seats=4),
        candidate_factory("static", revision_factory("r-s", available=False)),
        candidate_factory("late", revision_factory("r-l", arrival=3), free_seats=4),
        candidate_factory("empty", revision_factory("r-e", arrival=4), free_seats=0),
        candidate_factory(
            "big",
            revision_factory("r-b", arrival=5, capacity=6),
            free_seats=6,
            quote=quote_factory("q-b", 6),
        ),
    )

    result = allocate(candidates, 4, 0)

    named = {s.ship_id: s for s in result.trace if s.step in ("pick", "skip")}
    assert set(named) == {c.ship_id for c in candidates}
    assert named["picked"].step == "pick"
    assert all(named[ship].step == "skip" for ship in ("static", "late", "empty", "big"))
    assert all(dict(named[ship].detail)["reason"] for ship in ("static", "late", "empty", "big"))


@pytest.mark.parametrize("allocate", ALLOCATORS)
def test_trace_has_inputs_order_and_result_steps(allocate, candidate_factory, revision_factory):
    candidates = (
        candidate_factory("B", revision_factory("r-B", arrival=2), free_seats=3),
        candidate_factory("A", revision_factory("r-A", arrival=1), free_seats=3),
    )

    result = allocate(candidates, 4, 0)

    assert [s.step for s in result.trace][:2] == ["inputs", "order"]
    assert result.trace[-1].step == "result"
    assert dict(steps_of(result, "inputs")[0].detail) == {"candidates": "2", "demand": "4"}
    assert dict(steps_of(result, "result")[0].detail) == {"seats": "4", "remaining_demand": "0"}


def test_each_ordering_is_recorded_in_its_order_step(candidate_factory, revision_factory):
    candidates = (
        candidate_factory("A", revision_factory("r-A", arrival=9), free_seats=8),
        candidate_factory("B", revision_factory("r-B", arrival=1), free_seats=2),
    )

    earliest = allocate_earliest_arrival(candidates, 5, 0)
    largest = allocate_largest_capacity(candidates, 5, 0)

    assert dict(steps_of(earliest, "order")[0].detail)["ship_ids"] == "B,A"
    assert dict(steps_of(largest, "order")[0].detail)["ship_ids"] == "A,B"
    assert earliest.algorithm != largest.algorithm


@pytest.mark.parametrize("allocate", ALLOCATORS)
def test_empty_candidates_trace_has_only_inputs_order_and_result(allocate):
    result = allocate((), 5, 0)

    assert result.allocations == ()
    assert [s.step for s in result.trace] == ["inputs", "order", "result"]
    assert dict(result.trace[-1].detail) == {"seats": "0", "remaining_demand": "5"}


@pytest.mark.parametrize("allocate", ALLOCATORS)
def test_zero_seat_ship_and_oversized_quote_skips_carry_reasons(
    allocate, candidate_factory, revision_factory, quote_factory
):
    empty = candidate_factory("empty", revision_factory("r-x", arrival=1), free_seats=0)
    big = candidate_factory(
        "big",
        revision_factory("r-b", arrival=2, capacity=6),
        free_seats=6,
        quote=quote_factory("q", 6),
    )

    result = allocate((empty, big), 5, 0)
    skips = {s.ship_id: dict(s.detail)["reason"] for s in steps_of(result, "skip")}

    assert set(skips) == {"empty", "big"}
    assert skips == {"empty": "not_chosen", "big": "not_chosen"}
