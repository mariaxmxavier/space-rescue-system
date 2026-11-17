from __future__ import annotations

import pytest
from rescue.mobilisation.models.algorithm_name import AlgorithmName

from rescue.mobilisation import models
from rescue.mobilisation.models.policy import MobilisationPolicy
from rescue.values import DomainValidationError


def _policy(**overrides):
    values = {
        "policy_id": "p1",
        "revision": 1,
        "name": "Fast",
        "selection_criteria": "earliest_arrival",
    }
    return MobilisationPolicy(**{**values, **overrides})


def test_policy_is_importable_from_the_package_path():
    assert models.MobilisationPolicy is MobilisationPolicy


@pytest.mark.parametrize("revision", [0, -1])
def test_policy_rejects_revision_below_one(revision):
    with pytest.raises(DomainValidationError):
        _policy(revision=revision)


def test_policy_rejects_blank_name():
    with pytest.raises(DomainValidationError, match="policy name must be a nonblank string"):
        _policy(name=" ")


def test_policy_rejects_malformed_selection_criteria_entries():
    with pytest.raises(DomainValidationError, match="key/value pairs"):
        _policy(selection_criteria=(("a",),))


def test_policy_sorts_mapping_criteria_into_an_immutable_tuple():
    policy = _policy(selection_criteria={"strategy": "largest_capacity", "a": "b"})

    assert policy.selection_criteria == (("a", "b"), ("strategy", "largest_capacity"))
    assert policy.strategy == "largest_capacity"


def test_policy_strategy_falls_back_to_a_single_criterion_value():
    assert _policy(selection_criteria={"x": "earliest_arrival"}).strategy == "earliest_arrival"


def test_policy_without_a_named_strategy_fails_at_construction():
    with pytest.raises(DomainValidationError):
        _policy(selection_criteria={"a": "b", "c": "d"})


@pytest.mark.parametrize("name", list(AlgorithmName))
def test_policy_accepts_every_allowed_strategy_as_a_string(name):
    assert _policy(selection_criteria=name.value).strategy is name


@pytest.mark.parametrize("name", list(AlgorithmName))
def test_policy_accepts_every_allowed_strategy_as_key_value_pairs(name):
    assert _policy(selection_criteria=(("strategy", name.value),)).strategy is name


@pytest.mark.parametrize("name", list(AlgorithmName))
def test_policy_accepts_every_allowed_strategy_as_a_mapping(name):
    assert _policy(selection_criteria={"strategy": name.value}).strategy is name


@pytest.mark.parametrize("bad", ["fastest", "EARLIEST_ARRIVAL", "earliest arrival", "random"])
def test_policy_rejects_unknown_string_strategy_during_construction(bad):
    with pytest.raises(DomainValidationError):
        _policy(selection_criteria=bad)


@pytest.mark.parametrize(
    "criteria",
    [
        {"strategy": "fastest"},
        (("strategy", "fastest"),),
        {"x": "fastest"},
        {"strategy": "fastest", "a": "b"},
    ],
)
def test_policy_rejects_unknown_key_value_strategy_during_construction(criteria):
    with pytest.raises(DomainValidationError):
        _policy(selection_criteria=criteria)
