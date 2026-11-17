"""Rule `find_rfq` of the Procurement category. Documented in find_rfq.md.

When: called by `hold_quote` before a quote is held.
Why: an RFQ id must resolve to exactly one RFQ, or the quote's ship is ambiguous.
Diagram: ShipMarket class-diagram.mmd, `B3Market` --> `SeatRFQ`.
"""

from __future__ import annotations

from rescue.market.models.b3_market import B3Market
from rescue.market.models.procurement.seat_rfq import SeatRFQ
from rescue.values import DomainValidationError


def find_rfq(market: B3Market, rfq_id: str) -> SeatRFQ:
    """Return the one RFQ with `rfq_id`, or refuse.

    When: a ship's quote arrives and must be matched to the RFQ it answers.
    Why: a missing or duplicated RFQ would let a quote land on the wrong ship.
    Diagram: ShipMarket class-diagram.mmd (namespaces/ShipMarket).
    """
    matches = [rfq for rfq in market.rfqs if rfq.rfq_id == rfq_id]
    if len(matches) != 1:
        raise DomainValidationError("RFQ identity must resolve exactly once")
    return matches[0]
