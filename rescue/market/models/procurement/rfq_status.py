"""RFQStatus value of the Procurement category.

When: set on every SeatRFQ; changed to QUOTED when a ship's quote is held.
Why: a closed vocabulary stops typos; members equal their old strings, so callers keep working.
Diagram: ShipMarket class-diagram.mmd `RFQStatus`.
"""

from __future__ import annotations

from enum import StrEnum


class RFQStatus(StrEnum):
    """Where an RFQ is in its life: waiting, answered, or timed out.

    When: read before a quote is held, to make sure the RFQ is still open.
    Why: an RFQ gets at most one answer.
    Diagrams: ShipMarket class-diagram.mmd and entity-relationship-diagram.mmd.
    """

    PENDING = "pending"
    QUOTED = "quoted"
    EXPIRED = "expired"
