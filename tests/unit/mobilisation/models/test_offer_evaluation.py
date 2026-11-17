from __future__ import annotations

import pytest

from rescue.mobilisation import models
from rescue.mobilisation.models.offer_evaluation import OfferEvaluation
from rescue.values import DomainValidationError


def _evaluation(revision, **overrides):
    values = {
        "evaluation_id": "e1",
        "rank": 1,
        "proposed_seats": 2,
        "selected": True,
        "reason": None,
        "revision": revision,
        "ship_id": "s1",
    }
    return OfferEvaluation(**{**values, **overrides})


def test_offer_evaluation_is_importable_from_the_package_path():
    assert models.OfferEvaluation is OfferEvaluation


def test_selected_evaluation_with_seats_and_no_reason_is_valid(revision_factory):
    assert _evaluation(revision_factory("r1")).selected is True


def test_skipped_evaluation_with_reason_and_zero_seats_is_valid(revision_factory):
    skipped = _evaluation(
        revision_factory("r1"), selected=False, reason="unavailable", proposed_seats=0
    )

    assert skipped.reason == "unavailable"


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"reason": "x"}, "selected evaluations cannot have a skip reason"),
        ({"proposed_seats": 0}, "selected evaluations must propose a positive quantity"),
        ({"selected": False, "proposed_seats": 0}, "skipped evaluations require a reason"),
        (
            {"selected": False, "reason": "x", "proposed_seats": 1},
            "skipped evaluations cannot propose seats",
        ),
        ({"selected": 1}, "selected must be boolean"),
        ({"reason": " ", "selected": False, "proposed_seats": 0}, "evaluation reason"),
        ({"quote": "q"}, "evaluation quote must be an RFQOffer or None"),
    ],
)
def test_offer_evaluation_rejects_inconsistent_values(revision_factory, overrides, message):
    with pytest.raises(DomainValidationError, match=message):
        _evaluation(revision_factory("r1"), **overrides)


def test_offer_evaluation_rejects_rank_below_one(revision_factory):
    with pytest.raises(DomainValidationError):
        _evaluation(revision_factory("r1"), rank=0)


def test_offer_evaluation_rejects_a_non_revision():
    with pytest.raises(
        DomainValidationError, match="evaluation revision must be a ShipOfferRevision"
    ):
        _evaluation("r1")
