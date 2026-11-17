"""Candidate: a ship offer snapshot considered for one decision.

Transient value, not in the Mobilisation diagrams.
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.market.models import RFQOffer, ShipOfferRevision
from rescue.values import (
    DomainValidationError,
    Id,
    Instant,
    normalize_id,
    normalize_nonnegative_quantity,
)


@dataclass(frozen=True, slots=True)
class Candidate:
    """A ship offer revision with its free seats and optional quote, ready for selection.

    Built for each decision and discarded afterwards. It gathers what the selection rules
    need into one value. Transient: it is not persisted and is not a Mobilisation diagram
    class.
    """

    ship_id: Id
    revision: ShipOfferRevision
    free_seats: int
    quote: RFQOffer | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.revision, ShipOfferRevision):
            raise DomainValidationError("candidate revision must be a ShipOfferRevision")
        object.__setattr__(self, "ship_id", normalize_id(self.ship_id))
        object.__setattr__(self, "free_seats", normalize_nonnegative_quantity(self.free_seats))
        if self.quote is not None and not isinstance(self.quote, RFQOffer):
            raise DomainValidationError("candidate quote must be an RFQOffer or None")

    @property
    def allocatable_seats(self) -> int:
        """Seats the ship can give now: free seats capped by the revision capacity."""
        return min(self.free_seats, self.revision.capacity)


def arrival_instant(candidate: Candidate) -> Instant:
    """Return when the candidate ship arrives: revision record time plus its estimate.

    Used by every allocator to order ships by arrival so they share one definition.
    """
    return candidate.revision.recorded_at + candidate.revision.arrival_estimate_seconds
