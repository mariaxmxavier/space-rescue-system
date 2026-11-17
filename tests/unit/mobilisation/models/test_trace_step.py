from __future__ import annotations

import dataclasses

import pytest
from rescue.mobilisation.models.algorithm_name import AlgorithmName
from rescue.mobilisation.models.trace_step import TraceStep


def _step(**overrides):
    values = {
        "algorithm": AlgorithmName.KNAPSACK,
        "step": "pick",
        "ship_id": "A",
        "detail": (("seats", "3"),),
    }
    return TraceStep(**{**values, **overrides})


def test_trace_step_keeps_its_fields():
    step = _step()

    assert step.algorithm is AlgorithmName.KNAPSACK
    assert step.step == "pick"
    assert step.ship_id == "A"
    assert step.detail == (("seats", "3"),)


def test_trace_step_allows_no_ship():
    assert _step(ship_id=None).ship_id is None


@pytest.mark.parametrize("field", ["algorithm", "step", "ship_id", "detail"])
def test_trace_step_is_immutable(field):
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(_step(), field, None)


def test_trace_step_detail_is_a_tuple_of_pairs():
    assert isinstance(_step().detail, tuple)
    assert all(isinstance(pair, tuple) and len(pair) == 2 for pair in _step().detail)


def test_trace_step_is_hashable_because_it_is_immutable():
    assert hash(_step()) == hash(_step())
