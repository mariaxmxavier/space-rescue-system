"""Find a request for quotes in the run's market.

What: returns the RFQ with this id, or None when the market has none.
When called: by record_quote, accept_quote and open_request.
Why: every command that works on a quote starts from its RFQ.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from rescue.market.models.procurement import SeatRFQ
from rescue.state import RunState


def find_rfq(state: RunState, rfq_id: str) -> SeatRFQ | None:
    """Find rfq.

    What: returns the RFQ with this id from the market, or None.
    When called: by open_request, accept_quote and record_quote.
    Why: one lookup definition for every service that reads an RFQ.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    return next((item for item in state.market.rfqs if item.rfq_id == rfq_id), None)
