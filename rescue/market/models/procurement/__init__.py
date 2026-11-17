"""Procurement category: which mission asked which ship for seats.

When: read when RFQs are sent to available ships and when a ship answers one.
Why: a quote is valid only as the answer to one open RFQ for one ship.
Diagram: ShipMarket class-diagram.mmd, namespace Procurement.

Import entities as `from rescue.market.models.procurement import RFQStatus` and rules from
`rescue.market.models.procurement.rules`.
"""

from rescue.market.models.procurement.rfq_status import RFQStatus
from rescue.market.models.procurement.seat_rfq import SeatRFQ

__all__ = ["RFQStatus", "SeatRFQ"]
