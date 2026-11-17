"""Tests for the SimulationResult value.

What: Checks the completion rules and the field normalisation of one run result.
When called: By pytest, in the unit suite for experiment models.
Why: A result must never claim completion without a completion time or with unmet demand.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
"""

from decimal import Decimal

import pytest

from rescue.experiments.models.run.simulation_result import SimulationResult


def result(**changes):
    values = {
        "completed": False,
        "confirmed_seats": 1,
        "unmet_demand": 1,
        "requests_sent": 2,
        "released_seats": 0,
    }
    values.update(changes)
    return SimulationResult(**values)


def test_defaults_leave_both_times_empty():
    value = result()
    assert value.confirmation_elapsed_seconds is None
    assert value.latest_arrival_estimate_seconds is None


def test_completed_result_with_zero_unmet_demand_and_time_is_accepted():
    value = result(completed=True, unmet_demand=0, confirmation_elapsed_seconds=4)
    assert value.confirmation_elapsed_seconds == Decimal(4)


def test_completed_result_needs_zero_unmet_demand_and_a_time():
    with pytest.raises(ValueError, match="completed results require"):
        result(completed=True, unmet_demand=1, confirmation_elapsed_seconds=4)
    with pytest.raises(ValueError, match="completed results require"):
        result(completed=True, unmet_demand=0)


def test_incomplete_result_cannot_have_a_completion_time():
    with pytest.raises(ValueError, match="incomplete results cannot"):
        result(confirmation_elapsed_seconds=4)


def test_completed_must_be_a_boolean():
    with pytest.raises(ValueError, match="completed must be boolean"):
        result(completed=1)


def test_counts_must_be_nonnegative_integers():
    for name in ("confirmed_seats", "unmet_demand", "requests_sent", "released_seats"):
        with pytest.raises(ValueError):
            result(**{name: -1})


def test_arrival_estimate_is_normalised_when_present():
    assert result(latest_arrival_estimate_seconds=5).latest_arrival_estimate_seconds == Decimal(5)
