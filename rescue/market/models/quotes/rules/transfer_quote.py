"""Rule `transfer_quote` of the Quotes category. Documented in transfer_quote.md.

When: called when a mission accepts a held quote and a pending seat request is created for it.
Why: moves seats from "held" to the request's "pending" in one step, so they count exactly once.
Diagram: ShipMarket class-diagram.mmd, `RFQOffer` --> `QuoteStatusChange`.
"""

from __future__ import annotations

from dataclasses import replace

from rescue.market.models.b3_market import B3Market, require_market
from rescue.market.models.quotes.quote_status import QuoteStatus
from rescue.market.models.quotes.quote_status_change import QuoteStatusChange
from rescue.market.models.quotes.rules._held_quote import find_quote, with_quote
from rescue.values import DomainValidationError, Instant, normalize_id, normalize_instant


def transfer_quote(market: B3Market, quote_id: str, request_id: str, now: Instant) -> B3Market:
    """Return a market where the held quote is accepted and linked to `request_id`.

    When: the mission accepts the quote and a pending seat request is created for it.
    Why: in one step the seats stop counting as "held" and start counting as the request's
    "pending" seats, so they are never counted twice or lost.
    Diagram: ShipMarket class-diagram.mmd (namespaces/ShipMarket).
    """
    require_market(market)
    normalized_request_id = normalize_id(request_id)
    instant = normalize_instant(now)
    quote = find_quote(market, normalize_id(quote_id))
    if quote.status is not QuoteStatus.HELD:
        raise DomainValidationError("only a held quote can transfer to a request")
    if instant >= quote.expires_at:
        raise DomainValidationError("quote is expired")
    accepted = replace(quote, status=QuoteStatus.ACCEPTED, request_id=normalized_request_id)
    change = QuoteStatusChange(quote.offer_id, QuoteStatus.ACCEPTED, instant, normalized_request_id)
    return with_quote(market, accepted, change)
