"""Immutable mobilisation policy, candidate, and decision values."""

from __future__ import annotations

from dataclasses import dataclass

from rescue.market.models.offers import ShipOfferRevision
from rescue.market.models.quotes import RFQOffer
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


def _name(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{field_name} must be a nonblank string")
    return value


def _selection_criteria(value: object) -> str | tuple[tuple[str, str], ...]:
    """Keep policy configuration immutable while allowing a named strategy."""
    if isinstance(value, str):
        return _name(value, "selection criteria")
    if isinstance(value, dict):
        value = tuple(value.items())
    try:
        criteria = immutable_tuple(value)
    except TypeError as error:
        raise DomainValidationError(
            "selection criteria must be a strategy name or key/value pairs"
        ) from error
    normalized: list[tuple[str, str]] = []
    for item in criteria:
        if not isinstance(item, tuple) or len(item) != 2:
            raise DomainValidationError("selection criteria entries must be key/value pairs")
        key = _name(item[0], "selection criteria key")
        entry = _name(item[1], "selection criteria value")
        normalized.append((key, entry))
    return tuple(sorted(normalized))


@dataclass(frozen=True, slots=True)
class MobilisationPolicy:
    policy_id: Id
    revision: int
    name: str
    selection_criteria: str | tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "policy_id", normalize_id(self.policy_id))
        object.__setattr__(self, "revision", normalize_positive_quantity(self.revision))
        object.__setattr__(self, "name", _name(self.name, "policy name"))
        object.__setattr__(self, "selection_criteria", _selection_criteria(self.selection_criteria))

    @property
    def strategy(self) -> str:
        if isinstance(self.selection_criteria, str):
            return self.selection_criteria
        criteria = dict(self.selection_criteria)
        strategy = criteria.get("strategy")
        if strategy is None and len(criteria) == 1:
            strategy = next(iter(criteria.values()))
        if strategy is None:
            raise DomainValidationError("selection criteria must name a strategy")
        return strategy


@dataclass(frozen=True, slots=True)
class Candidate:
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
        return min(self.free_seats, self.revision.capacity)


@dataclass(frozen=True, slots=True)
class DecisionContext:
    decision_id: Id
    recorded_at: Instant
    evaluation_ids: tuple[Id, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", normalize_id(self.decision_id))
        object.__setattr__(self, "recorded_at", normalize_instant(self.recorded_at))
        evaluation_ids = immutable_tuple(self.evaluation_ids)
        for evaluation_id in evaluation_ids:
            normalize_id(evaluation_id)
        if len(evaluation_ids) != len(set(evaluation_ids)):
            raise DomainValidationError("evaluation IDs must be unique")
        object.__setattr__(self, "evaluation_ids", evaluation_ids)

    @property
    def time(self) -> Instant:
        return self.recorded_at


@dataclass(frozen=True, slots=True)
class OfferEvaluation:
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


@dataclass(frozen=True, slots=True)
class MobilisationDecision:
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
        return tuple(evaluation for evaluation in self.evaluations if evaluation.selected)

    @property
    def skipped(self) -> tuple[OfferEvaluation, ...]:
        return tuple(evaluation for evaluation in self.evaluations if not evaluation.selected)
