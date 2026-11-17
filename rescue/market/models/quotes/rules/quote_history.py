"""Rule `quote_history` of the Quotes category. Documented in quote_history.md.

When: called when a maintainer, a report or a test needs to know what happened to a quote.
Why: a quote only shows its current status; its earlier states live in the market's history.
Diagram: ShipMarket class-diagram.mmd, `B3Market` --> `QuoteStatusChange`.
"""

from __future__ import annotations

from rescue.market.models.b3_market import B3Market, require_market
from rescue.market.models.quotes.quote_status_change import QuoteStatusChange


def quote_history(market: B3Market, quote_id: str) -> tuple[QuoteStatusChange, ...]:
    """Return every status change of one quote, in append order; empty if it has none.

    When: a maintainer, a report or a test needs to know what happened to a quote.
    Why: the quote itself only shows its current status.
    Diagram: ShipMarket class-diagram.mmd (namespaces/ShipMarket).
    """
    require_market(market)
    return tuple(change for change in market.quote_history if change.quote_id == quote_id)
