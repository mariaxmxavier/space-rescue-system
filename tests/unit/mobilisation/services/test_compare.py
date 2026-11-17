"""Comparison service tests: one metrics row per scenario and algorithm, with a fake clock."""

from __future__ import annotations

import logging

import pytest

from rescue.mobilisation.algorithms import ALLOCATORS
from rescue.mobilisation.models.algorithm_name import AlgorithmName
from rescue.mobilisation.models.allocation import Allocation, AllocationResult
from rescue.mobilisation.models.trace_step import TraceStep
from rescue.mobilisation.services.compare import compare

FIRST = AlgorithmName.EARLIEST_ARRIVAL
SECOND = AlgorithmName.LARGEST_CAPACITY
FIELDS = {
    "scenario",
    "algorithm",
    "seats_covered",
    "last_seat_arrival_s",
    "ships_used",
    "unused_seats",
    "runtime_ms",
}


def allocator_of(algorithm, seats_by_ship):
    def allocate(candidates, demand, at):
        return AllocationResult(
            algorithm=algorithm,
            allocations=tuple(
                Allocation(item.ship_id, seats_by_ship.get(item.ship_id, 0)) for item in candidates
            ),
            trace=(TraceStep(algorithm, f"{algorithm.value}-step", None, (("demand", demand),)),),
        )

    return allocate


def clock_of(*values):
    ticks = iter(values)
    return lambda: next(ticks)


def get(row, name):
    return row[name] if isinstance(row, dict) or hasattr(row, "keys") else getattr(row, name)


def rows_by_key(rows):
    return {(get(row, "scenario"), get(row, "algorithm")): row for row in rows}


@pytest.fixture
def scenarios(mission_factory, revision_factory, candidate_factory, decision_context_factory):
    shipped = (
        candidate_factory("A", revision_factory("a-r", arrival=5), free_seats=6),
        candidate_factory("B", revision_factory("b-r", arrival=9), free_seats=8),
        candidate_factory("C", revision_factory("c-r", arrival=1), free_seats=5),
    )
    idle = (candidate_factory("D", revision_factory("d-r", arrival=4), free_seats=5),)
    return {
        "shipped": (mission_factory(10), shipped, decision_context_factory(3, recorded_at=2)),
        "idle": (mission_factory(5), idle, decision_context_factory(1, recorded_at=2)),
        "empty": (mission_factory(5), (), decision_context_factory(0, recorded_at=2)),
    }


@pytest.fixture
def allocators():
    return {
        FIRST: allocator_of(FIRST, {"A": 4}),
        SECOND: allocator_of(SECOND, {"A": 6, "B": 4}),
    }


FAKE_CLOCK = (0.0, 0.25, 1.0, 1.5, 2.0, 4.0, 5.0, 5.125, 6.0, 6.5, 7.0, 7.25)


def test_one_row_per_scenario_and_algorithm_in_input_order(scenarios, allocators):
    rows = compare(scenarios, allocators, clock_of(*FAKE_CLOCK))

    assert [(get(row, "scenario"), get(row, "algorithm")) for row in rows] == [
        (name, algorithm) for name in scenarios for algorithm in allocators
    ]
    assert all(
        get(row, name) is not None or name == "last_seat_arrival_s"
        for row in rows
        for name in FIELDS
    )


def test_row_values_for_a_partly_covered_scenario(scenarios, allocators):
    rows = rows_by_key(compare(scenarios, allocators, clock_of(*FAKE_CLOCK)))

    first = rows[("shipped", FIRST)]
    assert get(first, "seats_covered") == 4
    assert get(first, "last_seat_arrival_s") == 3
    assert get(first, "ships_used") == 1
    assert get(first, "unused_seats") == 2


def test_row_values_for_a_fully_covered_scenario(scenarios, allocators):
    rows = rows_by_key(compare(scenarios, allocators, clock_of(*FAKE_CLOCK)))

    second = rows[("shipped", SECOND)]
    assert get(second, "seats_covered") == 10
    assert get(second, "last_seat_arrival_s") == 7
    assert get(second, "ships_used") == 2
    assert get(second, "unused_seats") == 4


def test_unused_seats_ignore_ships_that_were_not_chosen(scenarios, allocators):
    rows = rows_by_key(compare(scenarios, allocators, clock_of(*FAKE_CLOCK)))

    assert get(rows[("shipped", FIRST)], "unused_seats") == 2


def test_no_selection_row_has_no_arrival_and_no_ships(scenarios, allocators):
    rows = rows_by_key(compare(scenarios, allocators, clock_of(*FAKE_CLOCK)))

    for algorithm in (FIRST, SECOND):
        for name in ("idle", "empty"):
            row = rows[(name, algorithm)]
            assert get(row, "seats_covered") == 0
            assert get(row, "last_seat_arrival_s") is None
            assert get(row, "ships_used") == 0
            assert get(row, "unused_seats") == 0


def test_under_coverage_is_reported_as_seats_below_demand(scenarios, allocators):
    rows = rows_by_key(compare(scenarios, allocators, clock_of(*FAKE_CLOCK)))

    assert get(rows[("shipped", FIRST)], "seats_covered") < 10


def test_runtime_ms_comes_from_the_injected_clock(scenarios, allocators):
    rows = compare(scenarios, allocators, clock_of(*FAKE_CLOCK))

    assert [get(row, "runtime_ms") for row in rows] == [250, 500, 2000, 125, 500, 250]


def test_a_subset_of_allocators_yields_only_those_rows(scenarios):
    only = {SECOND: allocator_of(SECOND, {"A": 6, "B": 4})}

    rows = compare(scenarios, only, clock_of(*FAKE_CLOCK))

    assert [get(row, "algorithm") for row in rows] == [SECOND] * 3


def test_full_registry_gives_a_row_for_every_algorithm(scenarios):
    rows = compare({"shipped": scenarios["shipped"]}, ALLOCATORS, lambda: 0.0)

    assert [get(row, "algorithm") for row in rows] == list(ALLOCATORS)
    assert {get(row, "runtime_ms") for row in rows} == {0}


def test_compare_logs_the_allocator_trace_at_debug(scenarios, allocators, caplog):
    with caplog.at_level(logging.DEBUG, logger="rescue.mobilisation"):
        compare({"shipped": scenarios["shipped"]}, allocators, clock_of(*FAKE_CLOCK))

    steps = [
        record.step
        for record in caplog.records
        if record.name == "rescue.mobilisation" and record.levelno == logging.DEBUG
    ]
    assert steps == [f"{FIRST.value}-step", f"{SECOND.value}-step"]
