"""ShipOffer entity of the Offers category.

When: created on a ship's first offer to a mission; grows by one revision per change.
Why: one logical offer per (mission, ship) pair, with its full revision history.
Diagram: ShipMarket class-diagram.mmd `ShipOffer` *-- `ShipOfferRevision`; ER `ShipOffer`.
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.market.models.offers.ship_offer_revision import ShipOfferRevision
from rescue.values import DomainValidationError, Id, immutable_tuple, normalize_id


@dataclass(frozen=True, slots=True)
class ShipOffer:
    """A ship's offer to one mission, with every revision it has had.

    When: read by mobilisation policies (current revision) and by request history (pinned one).
    Why: keeping all revisions lets the market show what was offered at any point.
    Diagrams: ShipMarket class-diagram.mmd and entity-relationship-diagram.mmd.
    """

    offer_id: Id
    mission_id: Id
    ship_id: Id
    revisions: tuple[ShipOfferRevision, ...]

    def __post_init__(self) -> None:
        """Validate on every construction: at least one revision, revision numbers unique."""
        normalize_id(self.offer_id)
        normalize_id(self.mission_id)
        normalize_id(self.ship_id)
        revisions = immutable_tuple(self.revisions)
        if not revisions:
            raise DomainValidationError("ship offer requires at least one revision")
        numbers = [revision.revision_number for revision in revisions]
        if len(numbers) != len(set(numbers)):
            raise DomainValidationError("ship offer revision numbers must be unique")
        object.__setattr__(self, "revisions", revisions)

    @property
    def current_revision(self) -> ShipOfferRevision:
        """The revision with the highest number; used whenever the offer's current terms are read."""
        return max(self.revisions, key=lambda revision: revision.revision_number)
