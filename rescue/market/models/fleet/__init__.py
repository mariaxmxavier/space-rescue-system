"""Fleet category: which ships exist.

When: read when a ship is registered or looked up by id.
Why: every other market category refers to a ship; the fleet is the list they refer to.
Diagram: ShipMarket class-diagram.mmd, namespace Fleet.

Import entities as `from rescue.market.models.fleet import Ship`; the fleet has no rules of
its own.
"""

from rescue.market.models.fleet.ship import Ship

__all__ = ["Ship"]
