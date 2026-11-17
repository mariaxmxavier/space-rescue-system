"""Availability category: how many seats a ship has right now.

When: read before every hold and every usage calculation.
Why: capacity changes over time; the append-only history of publications says what counts now.
Diagram: ShipMarket class-diagram.mmd, namespace Availability.

Import entities as `from rescue.market.models.availability import ShipAvailability` and rules from
`rescue.market.models.availability.rules`.
"""

from rescue.market.models.availability.ship_availability import ShipAvailability

__all__ = ["ShipAvailability"]
