"""Find a quote in the run's market.

What: returns the quote with this id, or None when the market has none.
When called: by accept_quote and reject_quote.
Why: both decisions on a quote look it up the same way.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from rescue.market.models.quotes import RFQOffer
from rescue.state import RunState


def find_quote(state: RunState, quote_id: str) -> RFQOffer | None:
    """Find quote.

    What: returns the quote with this offer id from the market, or None.
    When called: by accept_quote and reject_quote.
    Why: one lookup definition for every service that reads a quote.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    return next((item for item in state.market.quotes if item.offer_id == quote_id), None)
