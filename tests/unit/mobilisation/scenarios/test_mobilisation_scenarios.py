"""Checks that the shared mobilisation scenario fixture is complete, typed and immutable."""

from __future__ import annotations

from rescue.mission.models import Mission
from rescue.mobilisation.models import Candidate, DecisionContext, MobilisationPolicy

EXPECTED_KEYS = {
    "empty_inputs",
    "covered_demand",
    "exhausted_and_unavailable",
    "invalid_and_expired_holds",
    "oversized_hold",
    "deterministic_ties",
    "partial_capacity",
    "indivisible_undercoverage",
}


def test_scenarios_expose_exactly_the_eight_named_cases(mobilisation_scenarios):
    """The fixture offers exactly the eight edge cases the allocator contract needs."""
    assert set(mobilisation_scenarios) == EXPECTED_KEYS


def test_every_scenario_is_a_typed_four_tuple(mobilisation_scenarios):
    """Each scenario is mission, candidates, policy and decision context."""
    for scenario in mobilisation_scenarios.values():
        assert len(scenario) == 4
        mission, candidates, policy, context = scenario
        assert isinstance(mission, Mission)
        assert isinstance(candidates, tuple)
        assert all(isinstance(candidate, Candidate) for candidate in candidates)
        assert isinstance(policy, MobilisationPolicy)
        assert isinstance(context, DecisionContext)


def test_scenario_mapping_is_immutable(mobilisation_scenarios):
    """The mapping is a read-only proxy so tests cannot leak changes to each other."""
    assert type(mobilisation_scenarios).__name__ == "mappingproxy"
    try:
        mobilisation_scenarios["extra"] = ()
    except TypeError:
        return
    raise AssertionError("scenario mapping accepted an assignment")


def test_deterministic_ties_share_arrival_with_distinct_ships(mobilisation_scenarios):
    """Tied candidates have equal arrival 5 and unique ship ids."""
    _, candidates, _, _ = mobilisation_scenarios["deterministic_ties"]
    assert {c.revision.arrival_estimate_seconds for c in candidates} == {5}
    assert len({c.ship_id for c in candidates}) == len(candidates) > 1
