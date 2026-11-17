"""QuoteStatus value of the Quotes category.

When: set on every RFQOffer and on every QuoteStatusChange.
Why: a closed vocabulary stops typos; members equal their old strings, so callers keep working.
Diagram: ShipMarket class-diagram.mmd `QuoteStatus`.
"""

from __future__ import annotations

from enum import StrEnum


class QuoteStatus(StrEnum):
    """Where a quote is in its life.

    When: HELD on arrival; ACCEPTED when it becomes a seat request; REJECTED or EXPIRED when the
    hold ends without one.
    Why: only HELD quotes count as held seats; the others are history.
    Diagrams: ShipMarket class-diagram.mmd and entity-relationship-diagram.mmd.
    """

    HELD = "held"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
