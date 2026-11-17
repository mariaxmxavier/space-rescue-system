from __future__ import annotations

import dataclasses

import pytest

from rescue.mobilisation import models
from rescue.mobilisation.models.decision import MobilisationDecision
from rescue.mobilisation.models.offer_evaluation import OfferEvaluation
from rescue.values import DomainValidationError


def _evaluation(revision, number, *, selected=True):
    return OfferEvaluation(
        evaluation_id=f"e{number}",
        rank=number,
        proposed_seats=1 if selected else 0,
        selected=selected,
        reason=None if selected else "unavailable",
        revision=revision,
        ship_id=f"s{number}",
    )


def _decision(evaluations, **overrides):
    values = {
        "decision_id": "d1",
        "recorded_at": 0,
        "remaining_demand": 0,
        "evaluations": evaluations,
        "mission_id": "m1",
        "policy_id": "p1",
        "policy_revision": 1,
    }
    return MobilisationDecision(**{**values, **overrides})


def test_decision_is_importable_from_the_package_path():
    assert models.MobilisationDecision is MobilisationDecision


def test_decision_stores_evaluations_as_a_tuple_and_is_frozen(revision_factory):
    decision = _decision([_evaluation(revision_factory("r1"), 1)])

    assert isinstance(decision.evaluations, tuple)
    with pytest.raises(dataclasses.FrozenInstanceError):
        decision.remaining_demand = 3


def test_decision_splits_selected_and_skipped_views_in_rank_order(revision_factory):
    revision = revision_factory("r1")
    first, second, third = (
        _evaluation(revision, 1),
        _evaluation(revision, 2, selected=False),
        _evaluation(revision, 3),
    )
    decision = _decision((first, second, third))

    assert decision.selected == (first, third)
    assert decision.skipped == (second,)


def test_decision_rejects_non_contiguous_ranks(revision_factory):
    revision = revision_factory("r1")

    with pytest.raises(DomainValidationError, match="unique and contiguous"):
        _decision((_evaluation(revision, 1), _evaluation(revision, 3)))


def test_decision_rejects_duplicate_ranks(revision_factory):
    revision = revision_factory("r1")

    with pytest.raises(DomainValidationError, match="unique and contiguous"):
        _decision((_evaluation(revision, 1), _evaluation(revision, 1)))


def test_decision_rejects_duplicate_evaluation_ids(revision_factory):
    revision = revision_factory("r1")
    second = dataclasses.replace(_evaluation(revision, 2), evaluation_id="e1")

    with pytest.raises(DomainValidationError, match="evaluation IDs must be unique"):
        _decision((_evaluation(revision, 1), second))


def test_decision_rejects_non_evaluation_items():
    with pytest.raises(DomainValidationError, match="OfferEvaluation values"):
        _decision(("x",))


def test_decision_rejects_policy_revision_below_one():
    with pytest.raises(DomainValidationError):
        _decision((), policy_revision=0)


def test_decision_rejects_negative_remaining_demand():
    with pytest.raises(DomainValidationError):
        _decision((), remaining_demand=-1)
