from __future__ import annotations

from enum import StrEnum

import pytest

from rescue.mobilisation.models.skip_reason import SkipReason, static_skip_reason

EXPECTED = (
    "unavailable",
    "quote_not_held",
    "expired_quote",
    "insufficient_demand",
    "exhausted",
    "quote_exceeds_remaining_demand",
    "insufficient_capacity",
    "not_chosen",
)


def _held(candidate_factory, revision_factory, quote_factory, **quote_kwargs):
    return candidate_factory(
        "A", revision_factory("a-r"), quote=quote_factory("q", 2, **quote_kwargs)
    )


def test_skip_reason_is_a_string_enum_with_the_eight_reasons():
    assert issubclass(SkipReason, StrEnum)
    assert {member.value for member in SkipReason} == set(EXPECTED)
    assert len(SkipReason) == 8


def test_static_skip_reason_is_none_for_a_usable_candidate(candidate_factory, revision_factory):
    assert static_skip_reason(candidate_factory("A", revision_factory("a-r")), 0) is None


def test_static_skip_reason_flags_an_unavailable_ship(candidate_factory, revision_factory):
    candidate = candidate_factory("A", revision_factory("a-r", available=False))

    assert static_skip_reason(candidate, 0) is SkipReason.UNAVAILABLE


@pytest.mark.parametrize("status", ["rejected", "accepted", "expired"])
def test_static_skip_reason_flags_a_quote_that_is_not_held(
    status, candidate_factory, revision_factory, quote_factory
):
    candidate = _held(candidate_factory, revision_factory, quote_factory, status=status)

    assert static_skip_reason(candidate, 0) is SkipReason.QUOTE_NOT_HELD


def test_quote_is_still_held_one_unit_before_expiry(
    candidate_factory, revision_factory, quote_factory
):
    candidate = _held(candidate_factory, revision_factory, quote_factory, expires_at=20)

    assert static_skip_reason(candidate, 19) is None


@pytest.mark.parametrize("at", [20, 21])
def test_quote_is_expired_at_and_after_expires_at(
    at, candidate_factory, revision_factory, quote_factory
):
    candidate = _held(candidate_factory, revision_factory, quote_factory, expires_at=20)

    assert static_skip_reason(candidate, at) is SkipReason.EXPIRED_QUOTE


def test_unavailable_wins_over_quote_not_held(candidate_factory, revision_factory, quote_factory):
    candidate = candidate_factory(
        "A",
        revision_factory("a-r", available=False),
        quote=quote_factory("q", 2, status="rejected", expires_at=5),
    )

    assert static_skip_reason(candidate, 9) is SkipReason.UNAVAILABLE


def test_quote_not_held_wins_over_expired_quote(candidate_factory, revision_factory, quote_factory):
    candidate = _held(
        candidate_factory, revision_factory, quote_factory, status="rejected", expires_at=5
    )

    assert static_skip_reason(candidate, 9) is SkipReason.QUOTE_NOT_HELD


def test_unavailable_wins_over_expired_quote(candidate_factory, revision_factory, quote_factory):
    candidate = candidate_factory(
        "A", revision_factory("a-r", available=False), quote=quote_factory("q", 2, expires_at=5)
    )

    assert static_skip_reason(candidate, 9) is SkipReason.UNAVAILABLE


def test_static_skip_reason_ignores_capacity_reasons(candidate_factory, revision_factory):
    candidate = candidate_factory("A", revision_factory("a-r"), free_seats=0)

    assert static_skip_reason(candidate, 0) is None
