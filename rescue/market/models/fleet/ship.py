"""Ship entity of the Fleet category.

When: created when a ship is registered in the market.
Why: availability, RFQs and offers all point at a ship by `ship_id`.
Diagram: ShipMarket class-diagram.mmd `Ship`; entity-relationship-diagram.mmd `Ship`.
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import DomainValidationError, Id, normalize_id


@dataclass(frozen=True, slots=True)
class Ship:
    """A ship that can carry rescued people.

    When: built by the register-ship operation and by scenario set-up.
    Why: gives every seat count and offer a named, unique carrier.
    Diagrams: ShipMarket class-diagram.mmd and entity-relationship-diagram.mmd.
    """

    ship_id: Id
    name: str

    def __post_init__(self) -> None:
        """Validate on every construction so no ship without id or name can exist."""
        normalize_id(self.ship_id)
        if not isinstance(self.name, str) or not self.name.strip():
            raise DomainValidationError("ship name must be nonblank")
