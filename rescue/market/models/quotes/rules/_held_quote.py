"""Shared steps of the quote rules that change an existing quote (transfer and close).

When: used only by `transfer_quote` and `close_quote`.
Why: both must find exactly one quote and must replace it and append its history entry in the
same step; doing that in one place keeps quotes and history in sync.
Diagram: ShipMarket class-diagram.mmd (namespaces/ShipMarket).
"""

from __future__ import annotations

from dataclasses import replace

from rescue.market.models.b3_market import B3Market
from rescue.market.models.quotes.quote_status_change import QuoteStatusChange
from rescue.market.models.quotes.rfq_offer import RFQOffer
from rescue.values import DomainValidationError


def find_quote(market: B3Market, quote_id: str) -> RFQOffer:
    """Return the one quote with `quote_id`, or refuse.

    When: a transfer or close names the quote it acts on.
    Why: acting on a missing or duplicated quote would release or commit the wrong seats.
    Diagram: ShipMarket class-diagram.mmd (namespaces/ShipMarket).
    """
    matches = [quote for quote in market.quotes if quote.offer_id == quote_id]
    if len(matches) != 1:
        raise DomainValidationError("quote identity must resolve exactly once")
    return matches[0]


def with_quote(market: B3Market, quote: RFQOffer, change: QuoteStatusChange) -> B3Market:
    """Return a market with `quote` replaced and `change` appended to the quote history.

    When: the last step of a successful transfer or close.
    Why: a status change and its history entry must never be saved apart.
    Diagram: ShipMarket class-diagram.mmd (namespaces/ShipMarket).
    """
    return replace(
        market,
        quotes=tuple(quote if item.offer_id == quote.offer_id else item for item in market.quotes),
        quote_history=(*market.quote_history, change),
    )
