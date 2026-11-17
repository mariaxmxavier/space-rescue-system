"""RFQOffer entity of the Quotes category (a quote, or hold).

When: created when a ship answers an RFQ; its status changes on accept, reject or expiry.
Why: holding seats before the mission accepts stops two missions from taking the same seats.
Diagram: ShipMarket class-diagram.mmd `RFQOffer`; ER `RFQOffer`.
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.market.models.named_value import parse_named
from rescue.market.models.quotes.quote_status import QuoteStatus
from rescue.values import (
    DomainValidationError,
    Id,
    Instant,
    normalize_id,
    normalize_instant,
    normalize_positive_quantity,
)


@dataclass(frozen=True, slots=True)
class RFQOffer:
    """Seats a ship holds for one RFQ until accepted, rejected or expired.

    When: recorded by the record-quote operation; read by mobilisation to pick an offer.
    Why: an accepted quote must name the one seat request it became, so its seats move from
    "held" to "pending" exactly once.
    Diagrams: ShipMarket class-diagram.mmd and entity-relationship-diagram.mmd.
    """

    offer_id: Id
    rfq_id: Id
    offered_seats: int
    arrival_estimate_seconds: Instant
    expires_at: Instant
    recorded_at: Instant
    status: QuoteStatus = QuoteStatus.HELD
    request_id: Id | None = None

    def __post_init__(self) -> None:
        """Validate on every construction and `replace`; expiry follows recording."""
        normalize_id(self.offer_id)
        normalize_id(self.rfq_id)
        normalize_positive_quantity(self.offered_seats)
        object.__setattr__(
            self, "arrival_estimate_seconds", normalize_instant(self.arrival_estimate_seconds)
        )
        expiry = normalize_instant(self.expires_at)
        recorded = normalize_instant(self.recorded_at)
        if expiry <= recorded:
            raise DomainValidationError("quote expiry must follow its recorded time")
        object.__setattr__(self, "expires_at", expiry)
        object.__setattr__(self, "recorded_at", recorded)
        object.__setattr__(self, "status", parse_named(QuoteStatus, self.status, "quote status"))
        if self.request_id is not None:
            normalize_id(self.request_id)
        if (self.status is QuoteStatus.ACCEPTED) != (self.request_id is not None):
            raise DomainValidationError("accepted quotes require one linked request")
