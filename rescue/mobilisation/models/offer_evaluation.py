"""Offer evaluation: the ranked, explained outcome for one candidate.

Persisted entity. Diagram class: OfferEvaluation; UML and ER diagrams under
docs/architecture/diagrams/rescue-domain-model/namespaces/Mobilisation/.
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.market.models.offers import ShipOfferRevision
from rescue.market.models.quotes import RFQOffer
from rescue.mobilisation.models.policy import _name
from rescue.values import (
    DomainValidationError,
    Id,
    normalize_id,
    normalize_nonnegative_quantity,
    normalize_positive_quantity,
)


@dataclass(frozen=True, slots=True)
class OfferEvaluation:
    """The ranked outcome for one candidate: selected with seats, or skipped with a reason.

    Produced once per candidate when a decision is made and stored inside it. It makes
    each choice explainable afterwards. Diagram class: OfferEvaluation.
    """

    evaluation_id: Id
    rank: int
    proposed_seats: int
    selected: bool
    reason: str | None
    revision: ShipOfferRevision
    ship_id: Id
    quote: RFQOffer | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "evaluation_id", normalize_id(self.evaluation_id))
        object.__setattr__(self, "rank", normalize_positive_quantity(self.rank))
        object.__setattr__(
            self, "proposed_seats", normalize_nonnegative_quantity(self.proposed_seats)
        )
        if type(self.selected) is not bool:
            raise DomainValidationError("selected must be boolean")
        if self.reason is not None:
            object.__setattr__(self, "reason", _name(self.reason, "evaluation reason"))
        if self.selected and self.reason is not None:
            raise DomainValidationError("selected evaluations cannot have a skip reason")
        if not self.selected and self.reason is None:
            raise DomainValidationError("skipped evaluations require a reason")
        if self.selected and self.proposed_seats == 0:
            raise DomainValidationError("selected evaluations must propose a positive quantity")
        if not self.selected and self.proposed_seats != 0:
            raise DomainValidationError("skipped evaluations cannot propose seats")
        if not isinstance(self.revision, ShipOfferRevision):
            raise DomainValidationError("evaluation revision must be a ShipOfferRevision")
        object.__setattr__(self, "ship_id", normalize_id(self.ship_id))
        if self.quote is not None and not isinstance(self.quote, RFQOffer):
            raise DomainValidationError("evaluation quote must be an RFQOffer or None")
