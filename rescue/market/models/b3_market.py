"""B3Market aggregate: all market state of one run.

When: created with the run; replaced (never edited) by every market rule; saved as part of the
run state by the application's transaction store.
Why: one immutable value per run makes each market change all-or-nothing, and its tuples are
the market's history (availabilities, offer revisions, quote status changes).
Diagram: ShipMarket class-diagram.mmd `B3Market`; ER `B3Market`.
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.market.models.availability.ship_availability import ShipAvailability
from rescue.market.models.fleet.ship import Ship
from rescue.market.models.offers.ship_offer import ShipOffer
from rescue.market.models.procurement.seat_rfq import SeatRFQ
from rescue.market.models.quotes.quote_status_change import QuoteStatusChange
from rescue.market.models.quotes.rfq_offer import RFQOffer
from rescue.values import DomainValidationError, Id, immutable_tuple, normalize_id


@dataclass(frozen=True, slots=True)
class B3Market:
    """Ships, availability history, RFQs, quotes, offers and the quote history of one run.

    When: read and replaced inside one application transaction at a time.
    Why: persistence is the store's job; the market is a plain value the store can keep or
    discard whole, so a refused operation leaves nothing behind.
    Diagram: ShipMarket class-diagram.mmd (namespaces/ShipMarket).
    """

    market_id: Id
    ships: tuple[Ship, ...] = ()
    availabilities: tuple[ShipAvailability, ...] = ()
    rfqs: tuple[SeatRFQ, ...] = ()
    quotes: tuple[RFQOffer, ...] = ()
    offers: tuple[ShipOffer, ...] = ()
    quote_history: tuple[QuoteStatusChange, ...] = ()

    def __post_init__(self) -> None:
        """Validate the id and freeze every collection into a tuple on each construction."""
        normalize_id(self.market_id)
        for field_name in ("ships", "availabilities", "rfqs", "quotes", "offers", "quote_history"):
            object.__setattr__(self, field_name, immutable_tuple(getattr(self, field_name)))


def require_market(market: object) -> None:
    """Refuse anything that is not a B3Market.

    When: first line of every market rule.
    Why: rules are called from outside the market; a wrong argument must fail loudly at once.
    Diagram: ShipMarket class-diagram.mmd (namespaces/ShipMarket).
    """
    if not isinstance(market, B3Market):
        raise DomainValidationError("market operation requires a B3Market value")
