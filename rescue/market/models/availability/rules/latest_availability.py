"""Rule `latest_availability` of the Availability category. Documented in latest_availability.md.

When: called before a hold, before an RFQ is sent, and when usage is computed.
Why: publications are append-only history; this one rule decides which one counts.
Diagram: ShipMarket class-diagram.mmd, `Ship` --> `ShipAvailability`.
"""

from __future__ import annotations

from rescue.market.models.availability.ship_availability import ShipAvailability
from rescue.market.models.b3_market import B3Market, require_market
from rescue.values import DomainValidationError, normalize_id


def latest_availability(market: B3Market, ship_id: str) -> ShipAvailability | None:
    """Return the ship's publication with the latest `recorded_at`, or None if it has none.

    When: before a hold, before an RFQ is sent, and when usage is computed.
    Why: only the newest capacity counts; older ones stay as history. Two different
    publications at the same instant cannot be ordered, so they are refused.
    Diagram: ShipMarket class-diagram.mmd (namespaces/ShipMarket).
    """
    require_market(market)
    normalized_ship_id = normalize_id(ship_id)
    snapshots = [
        snapshot for snapshot in market.availabilities if snapshot.ship_id == normalized_ship_id
    ]
    if not snapshots:
        if not any(ship.ship_id == normalized_ship_id for ship in market.ships):
            raise DomainValidationError("unknown ship")
        return None
    latest_time = max(snapshot.recorded_at for snapshot in snapshots)
    latest = [snapshot for snapshot in snapshots if snapshot.recorded_at == latest_time]
    if len(set(latest)) > 1:
        raise DomainValidationError("conflicting availability snapshots share recorded_at")
    return latest[0]
