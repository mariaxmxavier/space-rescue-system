"""Unit tests for the OR-Tools min-cost flow allocator."""

from __future__ import annotations

from rescue.mobilisation.algorithms.greedy import allocate_earliest_arrival
from rescue.mobilisation.algorithms.min_cost_flow import allocate
from rescue.mobilisation.models import AlgorithmName


def seats_by_ship(result):
    return [(a.ship_id, a.seats) for a in result.allocations]


def steps(result, name):
    return [step for step in result.trace if step.step == name]


def test_covers_most_seats_then_prefers_earliest_arrival(candidate_factory, revision_factory):
    candidates = (
        candidate_factory("late", revision_factory("r-late", arrival=100), free_seats=5),
        candidate_factory("first", revision_factory("r-first", arrival=10), free_seats=3),
        candidate_factory("second", revision_factory("r-second", arrival=20), free_seats=3),
    )

    result = allocate(candidates, 5, 0)

    assert seats_by_ship(result) == [("first", 3), ("second", 2), ("late", 0)]


def test_takes_every_seat_when_demand_exceeds_supply(candidate_factory, revision_factory):
    candidates = (
        candidate_factory("A", revision_factory("r-A", arrival=9), free_seats=4),
        candidate_factory("B", revision_factory("r-B", arrival=1), free_seats=2),
    )

    result = allocate(candidates, 10, 0)

    assert seats_by_ship(result) == [("B", 2), ("A", 4)]


def test_held_quotes_are_preallocated_like_greedy(
    candidate_factory, revision_factory, quote_factory
):
    candidates = (
        candidate_factory(
            "q1", revision_factory("r-q1", capacity=4, arrival=1), quote=quote_factory("o1", 4)
        ),
        candidate_factory(
            "q2", revision_factory("r-q2", capacity=4, arrival=2), quote=quote_factory("o2", 4)
        ),
        candidate_factory("free", revision_factory("r-free", arrival=50)),
    )

    result = allocate(candidates, 6, 0)
    greedy = allocate_earliest_arrival(candidates, 6, 0)

    assert dict(seats_by_ship(result)) == dict(seats_by_ship(greedy))
    assert seats_by_ship(result) == [("q1", 4), ("free", 2), ("q2", 0)]


def test_held_quote_is_decided_before_earlier_unquoted_ship(
    candidate_factory, revision_factory, quote_factory
):
    candidates = (
        candidate_factory("open", revision_factory("r-open", arrival=1), free_seats=5),
        candidate_factory(
            "quoted",
            revision_factory("r-quoted", capacity=5, arrival=9),
            quote=quote_factory("o", 5),
        ),
    )

    result = allocate(candidates, 5, 0)

    assert seats_by_ship(result) == [("quoted", 5), ("open", 0)]


def test_exhausted_oversized_and_unusable_candidates_get_no_seats(
    candidate_factory, revision_factory, quote_factory
):
    candidates = (
        candidate_factory("empty", revision_factory("r-empty", arrival=1), free_seats=0),
        candidate_factory(
            "oversized",
            revision_factory("r-oversized", capacity=3, arrival=2),
            quote=quote_factory("o-big", 4),
        ),
        candidate_factory(
            "rejected",
            revision_factory("r-rejected", arrival=3),
            quote=quote_factory("o-rej", 2, status="rejected"),
        ),
        candidate_factory(
            "expired",
            revision_factory("r-expired", arrival=4),
            quote=quote_factory("o-exp", 2, expires_at=5),
        ),
        candidate_factory("down", revision_factory("r-down", arrival=5, available=False)),
    )

    result = allocate(candidates, 5, 5)

    assert all(seats == 0 for _, seats in seats_by_ship(result))
    assert [ship for ship, _ in seats_by_ship(result)] == [
        "empty",
        "oversized",
        "rejected",
        "expired",
        "down",
    ]


def test_ties_are_broken_by_ship_id(candidate_factory, revision_factory):
    candidates = tuple(
        candidate_factory(ship, revision_factory(f"r-{ship}", arrival=5), free_seats=2)
        for ship in ("C", "A", "B")
    )

    result = allocate(candidates, 3, 0)

    assert seats_by_ship(result) == [("A", 2), ("B", 1), ("C", 0)]


def test_sub_second_arrivals_keep_their_order(candidate_factory, revision_factory):
    candidates = (
        candidate_factory("A", revision_factory("r-A", arrival="0.7"), free_seats=2),
        candidate_factory("B", revision_factory("r-B", arrival="0.2"), free_seats=2),
    )

    result = allocate(candidates, 2, 0)

    assert seats_by_ship(result) == [("B", 2), ("A", 0)]


def test_arrival_cost_is_ceiled_whole_seconds_after_decision(candidate_factory, revision_factory):
    candidates = (
        candidate_factory("A", revision_factory("r-A", arrival="10.5", recorded_at=2)),
        candidate_factory("B", revision_factory("r-B", arrival=1)),
    )

    result = allocate(candidates, 1, 5)

    arcs = {step.ship_id: dict(step.detail) for step in steps(result, "arc")}
    assert arcs["A"]["arrival_cost_s"] == "8"
    assert arcs["B"]["arrival_cost_s"] == "0"


def test_zero_residual_demand_gives_flow_ships_nothing(
    candidate_factory, revision_factory, quote_factory
):
    candidates = (
        candidate_factory(
            "quoted", revision_factory("r-q", capacity=3, arrival=9), quote=quote_factory("o", 3)
        ),
        candidate_factory("open", revision_factory("r-open", arrival=1)),
    )

    covered = allocate(candidates, 3, 0)
    no_demand = allocate(candidates, 0, 0)

    assert seats_by_ship(covered) == [("quoted", 3), ("open", 0)]
    assert all(seats == 0 for _, seats in seats_by_ship(no_demand))
    assert dict(steps(covered, "model")[0].detail)["supply"] == "0"


def test_solver_failure_status_keeps_quotes_and_drops_flow(
    candidate_factory, revision_factory, quote_factory
):
    candidates = (
        candidate_factory("far", revision_factory("r-far", arrival=2**62)),
        candidate_factory(
            "quoted", revision_factory("r-q", capacity=2, arrival=1), quote=quote_factory("o", 2)
        ),
    )

    result = allocate(candidates, 5, 0)

    assert seats_by_ship(result) == [("quoted", 2), ("far", 0)]
    assert dict(steps(result, "status")[0].detail)["status"] == "BAD_COST_RANGE"


def test_trace_records_model_quotes_status_and_result_in_rank_order(
    candidate_factory, revision_factory, quote_factory
):
    candidates = (
        candidate_factory("open", revision_factory("r-open", arrival=3), free_seats=4),
        candidate_factory(
            "quoted", revision_factory("r-q", capacity=2, arrival=5), quote=quote_factory("o", 2)
        ),
        candidate_factory("spare", revision_factory("r-spare", arrival=1), free_seats=0),
    )

    result = allocate(candidates, 4, 0)

    assert result.algorithm == AlgorithmName.MIN_COST_FLOW
    assert {step.algorithm for step in result.trace} == {AlgorithmName.MIN_COST_FLOW}
    assert [step.step for step in result.trace][:2] == ["inputs", "quote"]
    assert dict(steps(result, "status")[0].detail)["status"] == "OPTIMAL"
    assert dict(steps(result, "model")[0].detail) == {"ships": "1", "supply": "2"}
    assert [(s.step, s.ship_id) for s in result.trace if s.step in ("pick", "skip")] == [
        ("pick", "open"),
        ("pick", "quoted"),
        ("skip", "spare"),
    ]
    assert result.trace[-1].step == "result"
    assert dict(result.trace[-1].detail) == {"seats": "4", "remaining_demand": "0"}
