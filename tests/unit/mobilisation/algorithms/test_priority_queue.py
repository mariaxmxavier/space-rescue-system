"""Tests for the priority-queue allocator: it must agree with greedy earliest arrival."""

from __future__ import annotations

from dataclasses import replace

from rescue.mobilisation.algorithms.greedy import allocate_earliest_arrival
from rescue.mobilisation.algorithms.priority_queue import allocate
from rescue.mobilisation.models.algorithm_name import AlgorithmName


def pairs(result):
    return [(a.ship_id, a.seats) for a in result.allocations]


def test_equals_greedy_earliest_arrival_on_every_scenario(mobilisation_scenarios):
    for name, (mission, candidates, _policy, _context) in mobilisation_scenarios.items():
        demand = mission.people_count
        queued = allocate(candidates, demand, 5)
        greedy = allocate_earliest_arrival(candidates, demand, 5)
        assert pairs(queued) == pairs(greedy), name
        assert queued.algorithm == AlgorithmName.PRIORITY_QUEUE


def test_recomputes_after_availability_change(candidate_factory, revision_factory):
    fast = candidate_factory("fast", revision_factory("r-fast", arrival=1), free_seats=4)
    slow = candidate_factory("slow", revision_factory("r-slow", arrival=9), free_seats=4)

    before = allocate((fast, slow), 6, 0)
    gone = replace(fast, revision=revision_factory("r-fast2", arrival=1, available=False))
    after = allocate((gone, slow), 6, 0)

    assert pairs(before) == [("fast", 4), ("slow", 2)]
    assert pairs(after) == [("fast", 0), ("slow", 4)]


def test_ties_break_by_ship_id(candidate_factory, revision_factory):
    candidates = tuple(
        candidate_factory(s, revision_factory(f"r-{s}", arrival=5), free_seats=1)
        for s in ("C", "A", "B")
    )

    result = allocate(candidates, 2, 0)

    assert pairs(result) == [("A", 1), ("B", 1), ("C", 0)]
    assert result == allocate(tuple(reversed(candidates)), 2, 0)


def test_held_quote_taken_whole_or_not_at_all(candidate_factory, revision_factory, quote_factory):
    big = candidate_factory(
        "a", revision_factory("r-a", arrival=1), free_seats=10, quote=quote_factory("qa", 6)
    )
    fits = candidate_factory(
        "b", revision_factory("r-b", arrival=2), free_seats=10, quote=quote_factory("qb", 3)
    )

    result = allocate((big, fits), 4, 0)

    assert pairs(result) == [("a", 0), ("b", 3)]


def test_empty_and_covered_demand(candidate_factory, revision_factory):
    ship = candidate_factory("s", revision_factory("r-s"))

    empty = allocate((), 5, 0)
    covered = allocate((ship,), 0, 0)

    assert empty.allocations == ()
    assert empty.trace[-1].step == "result"
    assert pairs(covered) == [("s", 0)]


def test_trace_has_step_per_candidate_in_rank_order_then_result(
    candidate_factory, revision_factory
):
    candidates = (
        candidate_factory("late", revision_factory("r-l", arrival=9), free_seats=2),
        candidate_factory("early", revision_factory("r-e", arrival=1), free_seats=2),
    )

    result = allocate(candidates, 3, 0)

    steps = [s for s in result.trace if s.ship_id is not None]
    assert [s.ship_id for s in steps] == ["early", "late"]
    assert result.trace[-1].step == "result"
    assert all(s.algorithm == AlgorithmName.PRIORITY_QUEUE for s in result.trace)
