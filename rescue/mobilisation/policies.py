"""Pure selection and explanation rules for mobilisation offers."""

from __future__ import annotations

from rescue.mission.models import Mission
from rescue.mission.rules import progress
from rescue.mobilisation.models import (
    Candidate,
    DecisionContext,
    MobilisationDecision,
    MobilisationPolicy,
    OfferEvaluation,
)
from rescue.values import DomainValidationError, immutable_tuple

_EARLIEST_ARRIVAL = "earliest_arrival"
_LARGEST_CAPACITY = "largest_capacity"


def _sort_key(strategy: str, candidate: Candidate) -> tuple[object, ...]:
    arrival_instant = candidate.revision.recorded_at + candidate.revision.arrival_estimate_seconds
    if strategy == _EARLIEST_ARRIVAL:
        return (arrival_instant, candidate.ship_id)
    return (-candidate.allocatable_seats, arrival_instant, candidate.ship_id)


def _skip_reason(
    candidate: Candidate,
    *,
    remaining_demand: int,
    recorded_at,
) -> str | None:
    if not candidate.revision.available:
        return "unavailable"
    if candidate.quote is not None:
        if candidate.quote.status != "held":
            return "quote_not_held"
        if candidate.quote.expires_at <= recorded_at:
            return "expired_quote"
    if remaining_demand <= 0:
        return "insufficient_demand"
    if candidate.allocatable_seats <= 0:
        return "exhausted"
    if candidate.quote is not None and candidate.quote.offered_seats > remaining_demand:
        return "quote_exceeds_remaining_demand"
    if candidate.quote is not None and candidate.quote.offered_seats > candidate.allocatable_seats:
        return "insufficient_capacity"
    return None


def select_offers(
    mission: Mission,
    candidates: tuple[Candidate, ...],
    policy: MobilisationPolicy,
    context: DecisionContext,
) -> MobilisationDecision:
    """Rank every candidate and propose seats without reserving market capacity."""
    if not isinstance(mission, Mission):
        raise DomainValidationError("select_offers requires a Mission")
    if not isinstance(policy, MobilisationPolicy):
        raise DomainValidationError("select_offers requires a MobilisationPolicy")
    if not isinstance(context, DecisionContext):
        raise DomainValidationError("select_offers requires a DecisionContext")
    candidates = immutable_tuple(candidates)
    if any(not isinstance(item, Candidate) for item in candidates):
        raise DomainValidationError("candidates must contain Candidate values")
    if len(context.evaluation_ids) != len(candidates):
        raise DomainValidationError("one evaluation ID is required for each candidate")
    ship_ids = tuple(item.ship_id for item in candidates)
    if len(ship_ids) != len(set(ship_ids)):
        raise DomainValidationError("candidates must contain at most one offer per ship")

    strategy = policy.strategy
    if strategy not in {_EARLIEST_ARRIVAL, _LARGEST_CAPACITY}:
        raise DomainValidationError(f"unknown mobilisation strategy: {strategy!r}")

    ordered = tuple(sorted(candidates, key=lambda item: _sort_key(strategy, item)))
    remaining_demand = progress(mission).additional_needed
    evaluations: list[OfferEvaluation] = []
    for rank, (candidate, evaluation_id) in enumerate(
        zip(ordered, context.evaluation_ids, strict=True), start=1
    ):
        reason = _skip_reason(
            candidate,
            remaining_demand=remaining_demand,
            recorded_at=context.recorded_at,
        )
        if reason is None:
            if candidate.quote is not None:
                proposed_seats = candidate.quote.offered_seats
            else:
                proposed_seats = min(candidate.allocatable_seats, remaining_demand)
            remaining_demand -= proposed_seats
            selected = True
        else:
            proposed_seats = 0
            selected = False
        evaluations.append(
            OfferEvaluation(
                evaluation_id=evaluation_id,
                rank=rank,
                proposed_seats=proposed_seats,
                selected=selected,
                reason=reason,
                revision=candidate.revision,
                ship_id=candidate.ship_id,
                quote=candidate.quote,
            )
        )

    return MobilisationDecision(
        decision_id=context.decision_id,
        recorded_at=context.recorded_at,
        remaining_demand=remaining_demand,
        evaluations=tuple(evaluations),
        mission_id=mission.mission_id,
        policy_id=policy.policy_id,
        policy_revision=policy.revision,
    )
