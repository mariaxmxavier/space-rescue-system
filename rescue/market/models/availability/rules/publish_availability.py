"""Rule `publish_availability` of the Availability category. Documented in publish_availability.md.

When: called by the publish-availability operation and by scenario steps.
Why: appending, never editing, keeps the availability history intact.
Diagram: ShipMarket class-diagram.mmd, `B3Market` --> `ShipAvailability`.
"""

from __future__ import annotations

from dataclasses import replace

from rescue.market.models.availability.ship_availability import ShipAvailability
from rescue.market.models.b3_market import B3Market, require_market
from rescue.values import DomainValidationError


def publish_availability(market: B3Market, availability: ShipAvailability) -> B3Market:
    """Return a market with `availability` appended to the history.

    When: a ship reports its seats (publish-availability operation, scenario steps).
    Why: appending, never editing, keeps history. Re-publishing the same value is a no-op so
    retries are safe; reusing an id or instant with different data is refused.
    Diagram: ShipMarket class-diagram.mmd (namespaces/ShipMarket).
    """
    require_market(market)
    if not isinstance(availability, ShipAvailability):
        raise DomainValidationError("availability must be a ShipAvailability value")
    if not any(ship.ship_id == availability.ship_id for ship in market.ships):
        raise DomainValidationError("availability references an unknown ship")
    for existing in market.availabilities:
        if existing.availability_id == availability.availability_id:
            if existing == availability:
                return market
            raise DomainValidationError("availability identity was reused with changed data")
        if (
            existing.ship_id == availability.ship_id
            and existing.recorded_at == availability.recorded_at
            and existing != availability
        ):
            raise DomainValidationError("conflicting availability at the same recorded_at")
    return replace(market, availabilities=(*market.availabilities, availability))
