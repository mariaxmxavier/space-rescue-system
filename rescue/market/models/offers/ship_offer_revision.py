"""ShipOfferRevision entity of the Offers category.

When: created each time a ship revises its offer to a mission.
Why: revisions are history; the highest `revision_number` is current, not the latest time.
Diagram: ShipMarket class-diagram.mmd `ShipOfferRevision`; ER `ShipOfferRevision`.
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import (
    DomainValidationError,
    Id,
    Instant,
    normalize_id,
    normalize_instant,
    normalize_positive_quantity,
)


@dataclass(frozen=True, slots=True)
class ShipOfferRevision:
    """One numbered version of a ship's offer: capacity, arrival estimate, availability.

    When: published by the publish-offer-revision operation; pinned by seat requests.
    Why: a seat request must keep the exact terms it was made against.
    Diagrams: ShipMarket class-diagram.mmd and entity-relationship-diagram.mmd.
    """

    revision_id: Id
    revision_number: int
    capacity: int
    arrival_estimate_seconds: Instant
    available: bool
    recorded_at: Instant

    def __post_init__(self) -> None:
        """Validate on every construction so a revision always has a positive number and capacity."""
        normalize_id(self.revision_id)
        normalize_positive_quantity(self.revision_number)
        normalize_positive_quantity(self.capacity)
        object.__setattr__(
            self, "arrival_estimate_seconds", normalize_instant(self.arrival_estimate_seconds)
        )
        object.__setattr__(self, "recorded_at", normalize_instant(self.recorded_at))
        if type(self.available) is not bool:
            raise DomainValidationError("available must be boolean")
