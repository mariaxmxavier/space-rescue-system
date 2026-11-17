"""Min-cost flow decides held quotes before open ships, whatever their arrival times."""

from rescue.market.models.offers import ShipOfferRevision
from rescue.market.models.quotes import RFQOffer
from rescue.mobilisation.algorithms.min_cost_flow.allocate import allocate
from rescue.mobilisation.models.candidate import Candidate


def _revision(revision_id: str, capacity: int, arrival: int) -> ShipOfferRevision:
    return ShipOfferRevision(
        revision_id=revision_id,
        revision_number=1,
        capacity=capacity,
        arrival_estimate_seconds=arrival,
        available=True,
        recorded_at=0,
    )


def test_late_quote_is_taken_before_an_earlier_open_ship() -> None:
    quote = RFQOffer(
        offer_id="Q-Q",
        rfq_id="R-Q",
        offered_seats=3,
        arrival_estimate_seconds=50,
        expires_at=100,
        recorded_at=1,
        status="held",
        request_id=None,
    )
    ships = (
        Candidate(ship_id="A", revision=_revision("A-r", 5, 1), free_seats=5),
        Candidate(ship_id="Q", revision=_revision("Q-r", 3, 50), free_seats=3, quote=quote),
    )
    result = allocate(ships, 5, 0)
    assert [(a.ship_id, a.seats) for a in result.allocations] == [("A", 2), ("Q", 3)]
