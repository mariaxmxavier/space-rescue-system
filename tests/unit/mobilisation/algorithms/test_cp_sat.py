"""Unit tests for the CP-SAT allocator: objectives, quotes, ties, statuses and trace."""

from __future__ import annotations

from decimal import Decimal

import pytest
from ortools.sat.python import cp_model

from rescue.mobilisation.algorithms import cp_sat as cp_sat_package
from rescue.mobilisation.algorithms.cp_sat import allocate
from rescue.mobilisation.models import AlgorithmName


def seats_by_ship(result):
    return [(a.ship_id, a.seats) for a in result.allocations]


def statuses(result):
    return [dict(step.detail)["status"] for step in result.trace if step.step == "status"]


def test_maximises_coverage_before_arrival(candidate_factory, revision_factory, quote_factory):
    candidates = (
        candidate_factory(
            "five", revision_factory("r5", capacity=5, arrival=1), quote=quote_factory("q5", 5)
        ),
        candidate_factory(
            "four", revision_factory("r4", capacity=4, arrival=2), quote=quote_factory("q4", 4)
        ),
        candidate_factory(
            "three", revision_factory("r3", capacity=3, arrival=3), quote=quote_factory("q3", 3)
        ),
    )

    result = allocate(candidates, 7, 0)

    assert seats_by_ship(result) == [("four", 4), ("three", 3), ("five", 0)]


def test_minimises_last_arrival_once_coverage_is_fixed(candidate_factory, revision_factory):
    candidates = (
        candidate_factory("A", revision_factory("rA", arrival=10), free_seats=5),
        candidate_factory("B", revision_factory("rB", arrival=1), free_seats=5),
        candidate_factory("C", revision_factory("rC", arrival=2), free_seats=5),
    )

    result = allocate(candidates, 10, 0)

    assert seats_by_ship(result) == [("B", 5), ("C", 5), ("A", 0)]


def test_uses_fewest_ships_at_equal_last_arrival(candidate_factory, revision_factory):
    candidates = (
        candidate_factory("A", revision_factory("rA", arrival=3), free_seats=5),
        candidate_factory("B", revision_factory("rB", arrival=3), free_seats=3),
        candidate_factory("C", revision_factory("rC", arrival=1), free_seats=2),
    )

    result = allocate(candidates, 5, 0)

    assert seats_by_ship(result) == [("A", 5), ("C", 0), ("B", 0)]


def test_fractional_arrivals_are_compared_exactly(candidate_factory, revision_factory):
    candidates = (
        candidate_factory("A", revision_factory("rA", recorded_at=Decimal("1.7")), free_seats=5),
        candidate_factory("B", revision_factory("rB", recorded_at=Decimal("1.2")), free_seats=5),
    )

    result = allocate(candidates, 5, 0)

    assert seats_by_ship(result) == [("B", 5), ("A", 0)]


def test_held_quote_is_whole_or_nothing(candidate_factory, revision_factory, quote_factory):
    quoted = candidate_factory(
        "quoted", revision_factory("rq", capacity=6), free_seats=6, quote=quote_factory("q", 4)
    )
    oversized = candidate_factory(
        "small", revision_factory("rs", capacity=3), free_seats=3, quote=quote_factory("qs", 4)
    )

    assert dict(seats_by_ship(allocate((quoted, oversized), 5, 0))) == {"quoted": 4, "small": 0}
    assert dict(seats_by_ship(allocate((quoted, oversized), 3, 0))) == {"quoted": 0, "small": 0}


@pytest.mark.parametrize("order", (("C", "B", "A"), ("A", "B", "C"), ("B", "C", "A")))
def test_equal_optimum_prefers_lowest_ship_id(order, candidate_factory, revision_factory):
    candidates = tuple(
        candidate_factory(ship, revision_factory(f"r{ship}", arrival=5), free_seats=5)
        for ship in order
    )

    assert seats_by_ship(allocate(candidates, 3, 0)) == [("A", 3), ("B", 0), ("C", 0)]
    assert seats_by_ship(allocate(candidates, 7, 0)) == [("A", 5), ("B", 2), ("C", 0)]


def test_empty_candidates_return_no_allocations():
    result = allocate((), 5, 0)

    assert result.allocations == ()
    assert result.algorithm is AlgorithmName.CP_SAT
    assert result.trace[-1].step == "result"


def test_zero_demand_and_static_skips_get_no_seats(
    candidate_factory, revision_factory, quote_factory
):
    candidates = (
        candidate_factory("ok", revision_factory("r-ok")),
        candidate_factory("unavailable", revision_factory("r-u", available=False)),
        candidate_factory(
            "expired", revision_factory("r-e"), quote=quote_factory("q-e", 2, expires_at=5)
        ),
    )

    assert sorted(seats_by_ship(allocate(candidates, 0, 5))) == [
        ("expired", 0),
        ("ok", 0),
        ("unavailable", 0),
    ]
    assert dict(seats_by_ship(allocate(candidates, 4, 5))) == {
        "ok": 4,
        "unavailable": 0,
        "expired": 0,
    }


def _solver_reporting(status):
    real_solver = cp_model.CpSolver

    def make():
        real = real_solver()

        class Reporting:
            parameters = real.parameters

            def solve(self, model):
                real.solve(model)
                return status

            def value(self, expression):
                return real.value(expression)

            @property
            def objective_value(self):
                return real.objective_value

        return Reporting()

    return make


@pytest.mark.parametrize(
    "status",
    (cp_model.INFEASIBLE, cp_model.MODEL_INVALID, cp_model.UNKNOWN),
)
def test_failed_solve_allocates_nothing_and_records_status(
    status, monkeypatch, candidate_factory, revision_factory
):
    monkeypatch.setattr(cp_model, "CpSolver", _solver_reporting(status))
    candidates = (candidate_factory("A", revision_factory("rA"), free_seats=5),)

    result = allocate(candidates, 5, 0)

    assert seats_by_ship(result) == [("A", 0)]
    assert statuses(result) == [status.name]


def test_feasible_status_is_accepted_and_recorded(monkeypatch, candidate_factory, revision_factory):
    monkeypatch.setattr(cp_model, "CpSolver", _solver_reporting(cp_model.FEASIBLE))
    candidates = (candidate_factory("A", revision_factory("rA"), free_seats=5),)

    result = allocate(candidates, 5, 0)

    assert seats_by_ship(result) == [("A", 5)]
    assert set(statuses(result)) == {"FEASIBLE"}


def test_optimal_statuses_are_recorded(candidate_factory, revision_factory):
    result = allocate((candidate_factory("A", revision_factory("rA"), free_seats=5),), 5, 0)

    assert statuses(result) and set(statuses(result)) == {"OPTIMAL"}


def test_repeated_runs_are_identical(candidate_factory, revision_factory, quote_factory):
    candidates = tuple(
        candidate_factory(
            f"S{index}", revision_factory(f"r{index}", arrival=index % 3), free_seats=4
        )
        for index in range(8)
    ) + (candidate_factory("Q", revision_factory("rQ"), quote=quote_factory("qQ", 3)),)

    results = [allocate(candidates, 13, 0) for _ in range(5)]

    assert all(result == results[0] for result in results)


def test_trace_lists_chosen_first_with_model_and_result(candidate_factory, revision_factory):
    candidates = (
        candidate_factory("late", revision_factory("r-late", arrival=9), free_seats=5),
        candidate_factory("early", revision_factory("r-early", arrival=1), free_seats=2),
        candidate_factory("mid", revision_factory("r-mid", arrival=4), free_seats=3),
        candidate_factory("off", revision_factory("r-off", available=False)),
    )

    result = allocate(candidates, 5, 0)
    steps = [(step.step, step.ship_id) for step in result.trace]

    assert seats_by_ship(result) == [("early", 2), ("mid", 3), ("off", 0), ("late", 0)]
    assert all(step.algorithm is AlgorithmName.CP_SAT for step in result.trace)
    assert steps[0] == ("model", None)
    assert [s for s in steps if s[0] in ("pick", "skip")] == [
        ("pick", "early"),
        ("pick", "mid"),
        ("skip", "off"),
        ("skip", "late"),
    ]
    assert steps[-1] == ("result", None)
    assert dict(result.trace[-1].detail)["seats"] == "5"


def test_package_exports_allocate():
    assert cp_sat_package.__all__ == ["allocate"]
