from __future__ import annotations

import pytest

from rescue.mobilisation import models
from rescue.mobilisation.models.candidate import Candidate
from rescue.values import DomainValidationError


def test_candidate_is_importable_from_the_package_path():
    assert models.Candidate is Candidate


def test_candidate_allocatable_seats_is_the_smaller_of_free_seats_and_capacity(revision_factory):
    revision = revision_factory("r1", capacity=4)

    assert Candidate("s1", revision, free_seats=9).allocatable_seats == 4
    assert Candidate("s1", revision, free_seats=3).allocatable_seats == 3


def test_candidate_accepts_zero_free_seats_and_rejects_negative(revision_factory):
    revision = revision_factory("r1")

    assert Candidate("s1", revision, free_seats=0).allocatable_seats == 0
    with pytest.raises(DomainValidationError):
        Candidate("s1", revision, free_seats=-1)


def test_candidate_rejects_a_non_revision():
    with pytest.raises(
        DomainValidationError, match="candidate revision must be a ShipOfferRevision"
    ):
        Candidate("s1", "r1", free_seats=1)


def test_candidate_rejects_a_quote_that_is_not_an_rfq_offer(revision_factory):
    with pytest.raises(DomainValidationError, match="candidate quote must be an RFQOffer or None"):
        Candidate("s1", revision_factory("r1"), free_seats=1, quote="q")


def test_candidate_keeps_a_valid_quote(revision_factory, quote_factory):
    quote = quote_factory("q1", 2)

    assert Candidate("s1", revision_factory("r1"), free_seats=1, quote=quote).quote is quote


def test_candidate_rejects_blank_ship_id(revision_factory):
    with pytest.raises(DomainValidationError):
        Candidate(" ", revision_factory("r1"), free_seats=1)
