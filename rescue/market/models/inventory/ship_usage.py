"""ShipUsage value of the Inventory category.

When: produced by `usage`; read before holds, by progress and by mobilisation policies.
Why: one derived snapshot of how a ship's seats are used; never stored, always recomputed.
Diagram: ShipMarket class-diagram.mmd `ShipUsage` (derived, so it has no ER entity).
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import normalize_nonnegative_quantity


@dataclass(frozen=True, slots=True)
class ShipUsage:
    """Seats of one ship: total, held, pending, confirmed, used, free and shortfall.

    When: computed at the moment a decision needs it.
    Why: `used = held + pending + confirmed`; `shortfall > 0` only when a later, lower
    availability fell below commitments made earlier.
    Diagrams: ShipMarket class-diagram.mmd and entity-relationship-diagram.mmd.
    """

    total: int
    held: int
    pending: int
    confirmed: int
    used: int
    free: int
    shortfall: int

    def __post_init__(self) -> None:
        """Validate on every construction: no count can be negative."""
        for field_name in ("total", "held", "pending", "confirmed", "used", "free", "shortfall"):
            normalize_nonnegative_quantity(getattr(self, field_name))
