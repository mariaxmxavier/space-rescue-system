"""Rule `hold_quote` of the Quotes category. Documented in hold_quote.md.

When: called by the record-quote operation when a ship answers an open RFQ.
Why: the only way seats become held, so the cross-mission capacity check lives here, once.
Diagram: ShipMarket class-diagram.mmd, `SeatRFQ` *-- `RFQOffer` --> `QuoteStatusChange`.
"""

from __future__ import annotations

from dataclasses import replace

from rescue.market.models.availability.rules.latest_availability import latest_availability
from rescue.market.models.b3_market import B3Market, require_market
from rescue.market.models.inventory.commitment_source import CommitmentSource
from rescue.market.models.inventory.rules.usage import usage
from rescue.market.models.procurement.rfq_status import RFQStatus
from rescue.market.models.procurement.rules.find_rfq import find_rfq
from rescue.market.models.quotes.quote_status import QuoteStatus
from rescue.market.models.quotes.quote_status_change import QuoteStatusChange
from rescue.market.models.quotes.rfq_offer import RFQOffer
from rescue.values import DomainValidationError, Instant, normalize_instant


def hold_quote(
    market: B3Market,
    commitments: tuple[CommitmentSource, ...],
    quote: RFQOffer,
    now: Instant,
) -> B3Market:
    """Return a market where `quote` holds its seats and its RFQ is marked quoted.

    When: a ship answers an open RFQ (record-quote operation).
    Why: the hold is accepted only if the ship is available now and has free seats after
    counting every other mission's holds and commitments, so no seat is counted twice.
    Diagram: ShipMarket class-diagram.mmd (namespaces/ShipMarket).
    """
    require_market(market)
    if not isinstance(quote, RFQOffer):
        raise DomainValidationError("quote must be an RFQOffer value")
    instant = normalize_instant(now)
    if instant < quote.recorded_at:
        raise DomainValidationError("quote cannot be recorded in the future")
    if instant >= quote.expires_at:
        raise DomainValidationError("quote is expired")
    if quote.status is not QuoteStatus.HELD or quote.request_id is not None:
        raise DomainValidationError("new quote response must be an unaccepted held quote")
    if any(existing.offer_id == quote.offer_id for existing in market.quotes):
        raise DomainValidationError("quote identity already exists")
    rfq = find_rfq(market, quote.rfq_id)
    if rfq.status is not RFQStatus.PENDING:
        raise DomainValidationError("RFQ already has a response or is expired")
    if quote.offered_seats > rfq.requested_seats:
        raise DomainValidationError("quote exceeds its RFQ quantity")
    snapshot = next(
        (item for item in market.availabilities if item.availability_id == rfq.availability_id),
        None,
    )
    if snapshot is None or snapshot.ship_id != rfq.ship_id or not snapshot.available:
        raise DomainValidationError("RFQ availability snapshot is invalid or unavailable")
    latest = latest_availability(market, rfq.ship_id)
    if latest is None or not latest.available:
        raise DomainValidationError("ship is currently unavailable")
    current_usage = usage(market, commitments, rfq.ship_id)
    if current_usage.shortfall:
        raise DomainValidationError("ship capacity is below existing commitments")
    if quote.offered_seats > current_usage.free:
        raise DomainValidationError("insufficient ship capacity for quote hold")
    quoted_rfq = replace(rfq, status=RFQStatus.QUOTED)
    return replace(
        market,
        rfqs=tuple(quoted_rfq if item.rfq_id == rfq.rfq_id else item for item in market.rfqs),
        quotes=(*market.quotes, quote),
        quote_history=(
            *market.quote_history,
            QuoteStatusChange(quote.offer_id, QuoteStatus.HELD, instant),
        ),
    )
