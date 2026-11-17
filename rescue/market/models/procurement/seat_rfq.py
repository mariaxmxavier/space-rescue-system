"""SeatRFQ entity of the Procurement category.

When: created when a mission asks the available ships for seats (one RFQ per ship).
Why: ties a mission's request to one ship and to the availability snapshot it saw.
Diagram: ShipMarket class-diagram.mmd `SeatRFQ`; ER `SeatRFQ`.
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.market.models.named_value import parse_named
from rescue.market.models.procurement.rfq_status import RFQStatus
from rescue.values import (
    DomainValidationError,
    Id,
    Instant,
    normalize_id,
    normalize_instant,
    normalize_positive_quantity,
)


@dataclass(frozen=True, slots=True)
class SeatRFQ:
    """A request for quote: one mission asks one ship for a number of seats.

    When: built by the send-RFQs operation; answered by at most one RFQOffer.
    Why: the referenced `availability_id` proves the ship was available when asked.
    Diagrams: ShipMarket class-diagram.mmd and entity-relationship-diagram.mmd.
    """

    rfq_id: Id
    mission_id: Id
    ship_id: Id
    availability_id: Id
    requested_seats: int
    status: RFQStatus
    sent_at: Instant
    response_deadline: Instant | None = None

    def __post_init__(self) -> None:
        """Validate on every construction and `replace`; the deadline must follow `sent_at`."""
        for identifier in (self.rfq_id, self.mission_id, self.ship_id, self.availability_id):
            normalize_id(identifier)
        normalize_positive_quantity(self.requested_seats)
        object.__setattr__(self, "status", parse_named(RFQStatus, self.status, "RFQ status"))
        object.__setattr__(self, "sent_at", normalize_instant(self.sent_at))
        if self.response_deadline is not None:
            deadline = normalize_instant(self.response_deadline)
            if deadline <= self.sent_at:
                raise DomainValidationError("RFQ response deadline must follow sent_at")
            object.__setattr__(self, "response_deadline", deadline)
