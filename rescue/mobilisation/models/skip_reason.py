"""Skip reason: why a candidate received no seats, and the rules fixed before allocation.

Read when a decision explains a zero allocation. Diagram: OfferEvaluation.reason.
"""

from __future__ import annotations

from enum import StrEnum

from rescue.mobilisation.models.candidate import Candidate
from rescue.values import Instant


class SkipReason(StrEnum):
    """The eight reasons a candidate can be skipped, in the order they are explained.

    Stored as the evaluation reason so every skipped ship carries a named cause.
    """

    UNAVAILABLE = "unavailable"
    QUOTE_NOT_HELD = "quote_not_held"
    EXPIRED_QUOTE = "expired_quote"
    INSUFFICIENT_DEMAND = "insufficient_demand"
    EXHAUSTED = "exhausted"
    QUOTE_EXCEEDS_REMAINING_DEMAND = "quote_exceeds_remaining_demand"
    INSUFFICIENT_CAPACITY = "insufficient_capacity"
    NOT_CHOSEN = "not_chosen"


def static_skip_reason(candidate: Candidate, at: Instant) -> SkipReason | None:
    """Return the first reason a candidate is unusable at the time, or None if usable.

    Called by allocators and the decision service before any seats are shared. It depends
    only on the candidate and the time, so every algorithm excludes the same candidates.
    """
    if not candidate.revision.available:
        return SkipReason.UNAVAILABLE
    quote = candidate.quote
    if quote is not None:
        if quote.status != "held":
            return SkipReason.QUOTE_NOT_HELD
        if quote.expires_at <= at:
            return SkipReason.EXPIRED_QUOTE
    return None
