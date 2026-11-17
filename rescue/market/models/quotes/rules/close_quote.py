"""Rule `close_quote` of the Quotes category. Documented in close_quote.md.

When: called when a mission declines a held quote, or when its expiry instant has passed.
Why: the only way held seats are released without becoming a request.
Diagram: ShipMarket class-diagram.mmd, `RFQOffer` --> `QuoteStatusChange`.
"""

from __future__ import annotations

from dataclasses import replace

from rescue.market.models.b3_market import B3Market, require_market
from rescue.market.models.quotes.quote_status import QuoteStatus
from rescue.market.models.quotes.quote_status_change import QuoteStatusChange
from rescue.market.models.quotes.rules._held_quote import find_quote, with_quote
from rescue.values import DomainValidationError, Instant, normalize_id, normalize_instant


def close_quote(market: B3Market, quote_id: str, status: str, now: Instant) -> B3Market:
    """Return a market where the held quote is rejected or expired, releasing its seats.

    When: the mission declines the quote, or its expiry instant has passed.
    Why: only an unaccepted hold can be released, and never before it expires on its own,
    so released seats are exactly the held ones.
    Diagram: ShipMarket class-diagram.mmd (namespaces/ShipMarket).
    """
    require_market(market)
    instant = normalize_instant(now)
    if status not in (QuoteStatus.REJECTED, QuoteStatus.EXPIRED):
        raise DomainValidationError("an unaccepted quote can only be rejected or expired")
    quote = find_quote(market, normalize_id(quote_id))
    if quote.status is not QuoteStatus.HELD:
        raise DomainValidationError("only unaccepted held quotes can be closed")
    if status == QuoteStatus.EXPIRED and instant < quote.expires_at:
        raise DomainValidationError("quote cannot expire before its expiry instant")
    if instant < quote.recorded_at:
        raise DomainValidationError("quote cannot close before it was recorded")
    closed = replace(quote, status=status)
    return with_quote(market, closed, QuoteStatusChange(quote.offer_id, closed.status, instant))
