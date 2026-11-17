"""Rule `usage` of the Inventory category. Documented in usage.md.

When: called before every hold, by progress, and by mobilisation when it ranks ships.
Why: this is the single place where a seat is counted, so it is counted exactly once.
Diagram: ShipMarket class-diagram.mmd, `ShipUsage` derived from `ShipAvailability`,
`RFQOffer` and `CommitmentSource`.
"""

from __future__ import annotations

from rescue.market.models.availability.rules.latest_availability import latest_availability
from rescue.market.models.b3_market import B3Market, require_market
from rescue.market.models.inventory.commitment_source import CommitmentSource
from rescue.market.models.inventory.ship_usage import ShipUsage
from rescue.market.models.quotes.quote_status import QuoteStatus
from rescue.values import DomainValidationError, normalize_id

_PENDING = "pending"
_CONFIRMED = frozenset({"accepted", "partially_accepted"})


def usage(market: B3Market, commitments: tuple[CommitmentSource, ...], ship_id: str) -> ShipUsage:
    """Return held, pending and confirmed seats of `ship_id` against its latest availability.

    When: a hold is checked, progress is reported, or a policy ranks ships.
    Why: held seats come from the market's HELD quotes; pending and confirmed seats come from
    the missions. An accepted quote is counted through its request only, never twice. An
    unavailable ship has no free seats, whatever its total.
    Diagram: ShipMarket class-diagram.mmd (namespaces/ShipMarket).
    """
    require_market(market)
    normalized_ship_id = normalize_id(ship_id)
    availability = latest_availability(market, normalized_ship_id)
    total = availability.total_seats if availability is not None else 0

    rfq_ships: dict[str, str] = {}
    for rfq in market.rfqs:
        if rfq.rfq_id in rfq_ships:
            raise DomainValidationError("RFQ identity must be unique in a market")
        rfq_ships[rfq.rfq_id] = rfq.ship_id
    seen_quotes: set[str] = set()
    held = 0
    for quote in market.quotes:
        if quote.offer_id in seen_quotes:
            raise DomainValidationError("quote identity must be unique in a market")
        seen_quotes.add(quote.offer_id)
        target_ship = rfq_ships.get(quote.rfq_id)
        if target_ship is None:
            raise DomainValidationError("quote must reference a known RFQ")
        if target_ship == normalized_ship_id and quote.status is QuoteStatus.HELD:
            held += quote.offered_seats

    pending = 0
    confirmed = 0
    seen_missions: set[str] = set()
    for source in commitments:
        if source.mission_id in seen_missions:
            raise DomainValidationError("mission identity must be unique in inventory view")
        seen_missions.add(source.mission_id)
        for request in source.requests:
            if request.ship_id != normalized_ship_id:
                continue
            if request.outcome == _PENDING:
                pending += request.requested_seats
            elif request.outcome in _CONFIRMED:
                confirmed += request.confirmed_seats

    used = held + pending + confirmed
    shortfall = max(0, used - total)
    free = max(0, total - used)
    if availability is not None and not availability.available:
        free = 0
    return ShipUsage(
        total=total,
        held=held,
        pending=pending,
        confirmed=confirmed,
        used=used,
        free=free,
        shortfall=shortfall,
    )
