"""ShipAvailability entity of the Availability category.

When: created each time a ship reports its seats; stored in `B3Market.availabilities`.
Why: the market keeps every publication (history) and counts only the latest per ship.
Diagram: ShipMarket class-diagram.mmd `ShipAvailability`; ER `ShipAvailability`.
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import (
    DomainValidationError,
    Id,
    Instant,
    normalize_id,
    normalize_instant,
    normalize_nonnegative_quantity,
)


@dataclass(frozen=True, slots=True)
class ShipAvailability:
    """A ship's seat count, arrival estimate and on/off state at one instant.

    When: published by a ship, then referenced by the RFQs sent while it was the latest.
    Why: an RFQ must show which capacity snapshot it was based on.
    Diagrams: ShipMarket class-diagram.mmd and entity-relationship-diagram.mmd.
    """

    availability_id: Id
    ship_id: Id
    total_seats: int
    arrival_estimate_seconds: Instant
    available: bool
    recorded_at: Instant

    def __post_init__(self) -> None:
        """Validate and normalise instants on every construction so snapshots compare exactly."""
        normalize_id(self.availability_id)
        normalize_id(self.ship_id)
        normalize_nonnegative_quantity(self.total_seats)
        object.__setattr__(
            self, "arrival_estimate_seconds", normalize_instant(self.arrival_estimate_seconds)
        )
        object.__setattr__(self, "recorded_at", normalize_instant(self.recorded_at))
        if type(self.available) is not bool:
            raise DomainValidationError("available must be boolean")
