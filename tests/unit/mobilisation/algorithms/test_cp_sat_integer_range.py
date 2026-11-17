"""CP-SAT rejects arrival offsets that do not fit the solver's integer range, as a domain error."""

from decimal import Decimal

import pytest

from rescue.market.models import ShipOfferRevision
from rescue.mobilisation.algorithms.cp_sat.allocate import allocate
from rescue.mobilisation.models.candidate import Candidate
from rescue.values import DomainValidationError


def _ship(ship_id: str, arrival: str) -> Candidate:
    revision = ShipOfferRevision(
        revision_id=f"{ship_id}-r",
        revision_number=1,
        capacity=2,
        arrival_estimate_seconds=Decimal(arrival),
        available=True,
        recorded_at=0,
    )
    return Candidate(ship_id=ship_id, revision=revision, free_seats=2)


def test_offsets_beyond_the_integer_range_are_rejected_as_a_domain_error() -> None:
    ships = (_ship("A", "0.0000000001"), _ship("B", "1000000000"))
    with pytest.raises(DomainValidationError, match="integer range"):
        allocate(ships, 3, Decimal(0))
