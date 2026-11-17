"""Tests for the 0/1 knapsack allocator: whole offers only, maximum seats, no overshoot."""

from __future__ import annotations

from importlib import import_module
from itertools import permutations

from rescue.mobilisation.algorithms.knapsack import allocate
from rescue.mobilisation.models.algorithm_name import AlgorithmName

allocate_module = import_module("rescue.mobilisation.algorithms.knapsack.allocate")


def seats_by_ship(result):
    return [(a.ship_id, a.seats) for a in result.allocations]


def steps(result, name):
    return [step for step in result.trace if step.step == name]


def test_package_exposes_the_module_allocate():
    assert allocate is allocate_module.allocate
    assert allocate((), 0, 0).algorithm == AlgorithmName.KNAPSACK


def test_whole_allocatable_offers_or_quoted_seats_only(
    candidate_factory, revision_factory, quote_factory
):
    candidates = (
        candidate_factory("open", revision_factory("r-open", capacity=4, arrival=1)),
        candidate_factory(
            "quoted",
            revision_factory("r-quoted", capacity=6, arrival=2),
            free_seats=6,
            quote=quote_factory("q", 3),
        ),
    )

    result = allocate(candidates, 7, 0)

    assert seats_by_ship(result) == [("open", 4), ("quoted", 3)]


def test_non_fitting_offers_are_not_chosen(candidate_factory, revision_factory, quote_factory):
    candidates = (
        candidate_factory("too-big", revision_factory("r-big", capacity=9, arrival=1)),
        candidate_factory(
            "quote-over-ship",
            revision_factory("r-q", capacity=3, arrival=2),
            free_seats=3,
            quote=quote_factory("q", 4),
        ),
        candidate_factory("fits", revision_factory("r-fits", capacity=2, arrival=3)),
    )

    result = allocate(candidates, 5, 0)

    assert dict(seats_by_ship(result)) == {"too-big": 0, "quote-over-ship": 0, "fits": 2}


def test_maximum_covered_seats_without_overshoot(candidate_factory, revision_factory):
    candidates = tuple(
        candidate_factory(ship, revision_factory(f"r-{ship}", capacity=cap, arrival=arrival))
        for ship, cap, arrival in (("A", 5, 1), ("B", 4, 2), ("C", 3, 3))
    )

    result = allocate(candidates, 7, 0)

    assert dict(seats_by_ship(result)) == {"A": 0, "B": 4, "C": 3}
    assert sum(seats for _, seats in seats_by_ship(result)) == 7


def test_under_coverage_is_visible_in_the_result_step(
    candidate_factory, revision_factory, quote_factory
):
    candidates = (
        candidate_factory(
            "quote-five",
            revision_factory("r5", capacity=5, arrival=1),
            quote=quote_factory("q5", 5),
        ),
        candidate_factory(
            "quote-four",
            revision_factory("r4", capacity=4, arrival=2),
            quote=quote_factory("q4", 4),
        ),
    )

    result = allocate(candidates, 7, 0)

    assert seats_by_ship(result) == [("quote-five", 5), ("quote-four", 0)]
    assert result.trace[-1].step == "result"
    assert dict(result.trace[-1].detail) == {"seats": "5", "remaining_demand": "2"}


def test_static_skips_get_zero_seats(candidate_factory, revision_factory, quote_factory):
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

    assert all(seats == 0 for _, seats in seats_by_ship(result))
    reasons = {step.ship_id: dict(step.detail)["reason"] for step in steps(result, "skip")}
    assert reasons == {
        "unavailable": "unavailable",
        "rejected": "quote_not_held",
        "expired": "expired_quote",
        "empty": "not_chosen",
    }


def test_tied_alternatives_choose_the_same_set_on_every_input_order(
    candidate_factory, revision_factory
):
    candidates = tuple(
        candidate_factory(ship, revision_factory(f"r-{ship}", capacity=3, arrival=5))
        for ship in ("C", "A", "B")
    )

    results = {tuple(seats_by_ship(allocate(order, 3, 0))) for order in permutations(candidates)}

    assert results == {(("A", 3), ("B", 0), ("C", 0))}


def test_chosen_first_rank_order_and_trace(candidate_factory, revision_factory):
    candidates = tuple(
        candidate_factory(ship, revision_factory(f"r-{ship}", capacity=cap, arrival=arrival))
        for ship, cap, arrival in (("A", 5, 1), ("B", 4, 2), ("C", 3, 3))
    )

    result = allocate(candidates, 7, 0)

    assert [ship for ship, _ in seats_by_ship(result)] == ["B", "C", "A"]
    assert all(step.algorithm == AlgorithmName.KNAPSACK for step in result.trace)
    assert [step.step for step in result.trace] == [
        "item",
        "item",
        "item",
        "model",
        "solver",
        "pick",
        "pick",
        "skip",
        "result",
    ]
    assert [dict(step.detail)["weight"] for step in steps(result, "item")] == ["5", "4", "3"]
    assert dict(steps(result, "model")[0].detail) == {"items": "3", "capacity": "7"}
    assert dict(steps(result, "solver")[0].detail) == {"status": "optimal", "seats": "7"}


def test_empty_branch_skips_the_solver(candidate_factory, revision_factory):
    unavailable = candidate_factory("U", revision_factory("r-u", available=False))

    no_demand = allocate((candidate_factory("A", revision_factory("r-a")),), 0, 0)
    no_items = allocate((), 4, 0)
    nothing_eligible = allocate((unavailable,), 4, 0)

    for result in (no_demand, no_items, nothing_eligible):
        assert dict(steps(result, "solver")[0].detail) == {"status": "empty", "seats": "0"}
        assert all(seats == 0 for _, seats in seats_by_ship(result))
    assert dict(no_items.trace[-1].detail) == {"seats": "0", "remaining_demand": "4"}


def test_non_optimal_branch_keeps_the_feasible_solution(
    monkeypatch, candidate_factory, revision_factory
):
    class FeasibleOnly:
        def __init__(self, *_args):
            self.chosen = ()

        def init(self, profits, _weights, _capacities):
            self.chosen = (0,)
            self.profits = profits

        def solve(self):
            return self.profits[0]

        def is_solution_optimal(self):
            return False

        def best_solution_contains(self, index):
            return index in self.chosen

    monkeypatch.setattr(allocate_module, "KnapsackSolver", FeasibleOnly)
    candidates = tuple(
        candidate_factory(ship, revision_factory(f"r-{ship}", capacity=cap, arrival=arrival))
        for ship, cap, arrival in (("A", 2, 1), ("B", 3, 2))
    )

    result = allocate(candidates, 5, 0)

    assert seats_by_ship(result) == [("A", 2), ("B", 0)]
    assert dict(steps(result, "solver")[0].detail) == {"status": "feasible", "seats": "2"}
