"""Mobilisation decision: the recorded outcome of applying a policy to offers.

Persisted entity. Diagram class: MobilisationDecision; UML and ER diagrams under
docs/architecture/diagrams/rescue-domain-model/namespaces/Mobilisation/.
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.mobilisation.models.offer_evaluation import OfferEvaluation
from rescue.values import (
    DomainValidationError,
    Id,
    Instant,
    immutable_tuple,
    normalize_id,
    normalize_instant,
    normalize_nonnegative_quantity,
    normalize_positive_quantity,
)


@dataclass(frozen=True, slots=True)
class MobilisationDecision:
    """The recorded result of applying one policy revision to a mission's offers.

    Created when a mobilisation decision is made and persisted with its ranked
    evaluations and the demand left unmet. It is the auditable answer to why these ships
    were chosen. Diagram class: MobilisationDecision.
    """

    decision_id: Id
    recorded_at: Instant
    remaining_demand: int
    evaluations: tuple[OfferEvaluation, ...]
    mission_id: Id
    policy_id: Id
    policy_revision: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", normalize_id(self.decision_id))
        object.__setattr__(self, "recorded_at", normalize_instant(self.recorded_at))
        object.__setattr__(
            self,
            "remaining_demand",
            normalize_nonnegative_quantity(self.remaining_demand),
        )
        evaluations = immutable_tuple(self.evaluations)
        if any(not isinstance(item, OfferEvaluation) for item in evaluations):
            raise DomainValidationError("decision evaluations must be OfferEvaluation values")
        ranks = tuple(item.rank for item in evaluations)
        evaluation_ids = tuple(item.evaluation_id for item in evaluations)
        if ranks != tuple(range(1, len(evaluations) + 1)):
            raise DomainValidationError("evaluation ranks must be unique and contiguous")
        if len(evaluation_ids) != len(set(evaluation_ids)):
            raise DomainValidationError("evaluation IDs must be unique")
        object.__setattr__(self, "evaluations", evaluations)
        object.__setattr__(self, "mission_id", normalize_id(self.mission_id))
        object.__setattr__(self, "policy_id", normalize_id(self.policy_id))
        object.__setattr__(
            self, "policy_revision", normalize_positive_quantity(self.policy_revision)
        )

    @property
    def selected(self) -> tuple[OfferEvaluation, ...]:
        """The evaluations that were chosen, in rank order."""
        return tuple(evaluation for evaluation in self.evaluations if evaluation.selected)

    @property
    def skipped(self) -> tuple[OfferEvaluation, ...]:
        """The evaluations that were passed over, in rank order."""
        return tuple(evaluation for evaluation in self.evaluations if not evaluation.selected)
