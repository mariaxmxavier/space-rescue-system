from __future__ import annotations

from enum import StrEnum

import pytest
from rescue.mobilisation.models.algorithm_name import AlgorithmName

EXPECTED = (
    "earliest_arrival",
    "largest_capacity",
    "priority_queue",
    "min_cost_flow",
    "cp_sat",
    "knapsack",
)


def test_algorithm_name_is_a_string_enum():
    assert issubclass(AlgorithmName, StrEnum)


def test_algorithm_name_has_exactly_the_six_allowed_values():
    assert {member.value for member in AlgorithmName} == set(EXPECTED)
    assert len(AlgorithmName) == 6


@pytest.mark.parametrize("value", EXPECTED)
def test_algorithm_name_resolves_from_its_string(value):
    assert AlgorithmName(value) == value
    assert AlgorithmName(value).value == value


@pytest.mark.parametrize("value", ["fastest", "", "EARLIEST_ARRIVAL"])
def test_algorithm_name_rejects_other_names(value):
    with pytest.raises(ValueError):
        AlgorithmName(value)
