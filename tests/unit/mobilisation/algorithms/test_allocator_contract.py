"""Contract tests every registered allocator must pass (allocator contract rules 1 to 7)."""

from __future__ import annotations

import pytest

from rescue.mission.rules import progress
from rescue.mobilisation.algorithms import ALLOCATORS, Allocator
from rescue.mobilisation.models.algorithm_name import AlgorithmName
from rescue.mobilisation.models.skip_reason import static_skip_reason

ALGORITHMS = tuple(AlgorithmName)
SCENARIO_NAMES = (
    "empty_inputs",
    "covered_demand",
    "exhausted_and_unavailable",
    "invalid_and_expired_holds",
    "oversized_hold",
    "deterministic_ties",
    "partial_capacity",
    "indivisible_undercoverage",
)


@pytest.fixture(params=ALGORITHMS, ids=lambda name: str(name))
def allocator(request) -> Allocator:
    """Resolve one registry entry so each test runs once per algorithm."""
    return ALLOCATORS[request.param]


@pytest.fixture(params=SCENARIO_NAMES)
def run(request, allocator, mobilisation_scenarios):
    """Run the allocator on one scenario and return its inputs and result."""
    mission, candidates, _policy, context = mobilisation_scenarios[request.param]
    demand = progress(mission).additional_needed
    at = context.recorded_at
    return candidates, demand, at, allocator(candidates, demand, at)


def test_registry_is_complete():
    assert set(ALLOCATORS) == set(AlgorithmName)
    assert all(callable(function) for function in ALLOCATORS.values())


def test_rule_1_every_input_exactly_once_in_rank_order(run):
    candidates, _demand, _at, result = run
    returned = [allocation.ship_id for allocation in result.allocations]
    assert sorted(returned) == sorted(c.ship_id for c in candidates)
    assert len(returned) == len(set(returned))


def test_rule_2_static_skips_get_zero_seats(run):
    candidates, _demand, at, result = run
    seats = {a.ship_id: a.seats for a in result.allocations}
    for candidate in candidates:
        if static_skip_reason(candidate, at) is not None:
            assert seats[candidate.ship_id] == 0


def test_rule_3_seats_within_allocatable(run):
    candidates, _demand, _at, result = run
    allocatable = {c.ship_id: c.allocatable_seats for c in candidates}
    for allocation in result.allocations:
        assert 0 <= allocation.seats <= allocatable[allocation.ship_id]


def test_rule_4_held_quote_is_indivisible(run):
    candidates, _demand, at, result = run
    seats = {a.ship_id: a.seats for a in result.allocations}
    for candidate in candidates:
        quote = candidate.quote
        if quote is not None and static_skip_reason(candidate, at) is None:
            assert seats[candidate.ship_id] in {0, quote.offered_seats}


def test_rule_5_total_seats_within_demand(run):
    _candidates, demand, _at, result = run
    assert sum(a.seats for a in result.allocations) <= demand


def test_rule_6_deterministic(allocator, run):
    candidates, demand, at, result = run
    assert allocator(candidates, demand, at) == result


def test_rule_6_equal_ties_pick_the_lowest_ship_ids(allocator, mobilisation_scenarios):
    """Equal arrivals and capacities fill the lowest ship ids first, and rank order is A, B, C.

    Knapsack ranks chosen ships first (rule 1: rank order as that allocator defines it), so
    its order is the chosen ships by id followed by the rest by id. Knapsack takes whole
    offers only, so a ship whose offer exceeds the remaining demand gets nothing.
    """
    mission, candidates, _policy, context = mobilisation_scenarios["deterministic_ties"]
    demand = progress(mission).additional_needed
    result = allocator(candidates, demand, context.recorded_at)
    seats = {a.ship_id: a.seats for a in result.allocations}
    capacity = {c.ship_id: c.allocatable_seats for c in candidates}
    remaining, expected = demand, {}
    for ship_id in sorted(capacity):
        take = min(capacity[ship_id], remaining)
        whole = allocator is ALLOCATORS[AlgorithmName.KNAPSACK]
        expected[ship_id] = take if not whole or take == capacity[ship_id] else 0
        remaining -= expected[ship_id]
    chosen = {ship_id for ship_id, count in seats.items() if count}
    assert chosen == {ship_id for ship_id, count in expected.items() if count}
    ids = [a.ship_id for a in result.allocations]
    assert ids == sorted(ids, key=lambda ship_id: (ship_id not in chosen, ship_id))


def test_rule_7_trace_has_a_step_per_candidate_and_final_result(run):
    candidates, _demand, _at, result = run
    traced = {step.ship_id for step in result.trace if step.ship_id is not None}
    assert {c.ship_id for c in candidates} <= traced
    assert result.trace[-1].step == "result"
    assert all(step.algorithm == result.algorithm for step in result.trace)
