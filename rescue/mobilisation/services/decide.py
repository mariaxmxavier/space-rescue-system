"""Decision service: run the configured allocator, check it, and explain every outcome.

Called once per decision. It keeps allocation strategies swappable while the checks and the
explanation of zero allocations stay in one place, so every algorithm yields the same shape.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping

from rescue.mission.models import Mission
from rescue.mission.rules import progress
from rescue.mobilisation.algorithms import ALLOCATORS, Allocator
from rescue.mobilisation.models import (
    AlgorithmName,
    AllocationResult,
    Candidate,
    DecisionContext,
    MobilisationDecision,
    MobilisationPolicy,
    OfferEvaluation,
    SkipReason,
    static_skip_reason,
)
from rescue.values import DomainValidationError, Instant, immutable_tuple

logger = logging.getLogger("rescue.mobilisation")


def _validate_allocation(
    result: AllocationResult,
    candidates: tuple[Candidate, ...],
    demand: int,
    context: DecisionContext,
) -> None:
    by_ship = {candidate.ship_id: candidate for candidate in candidates}
    ship_ids = [allocation.ship_id for allocation in result.allocations]
    if len(ship_ids) != len(set(ship_ids)) or set(ship_ids) != set(by_ship):
        raise DomainValidationError("allocator must return each candidate exactly once")
    for allocation in result.allocations:
        candidate = by_ship[allocation.ship_id]
        if allocation.seats and static_skip_reason(candidate, context.recorded_at) is not None:
            raise DomainValidationError("allocator gave seats to a skipped candidate")
        if allocation.seats > candidate.allocatable_seats:
            raise DomainValidationError("allocator exceeded a ship's allocatable seats")
        quote = candidate.quote
        if quote is not None and allocation.seats not in {0, quote.offered_seats}:
            raise DomainValidationError("allocator split a held quote")
    if sum(allocation.seats for allocation in result.allocations) > demand:
        raise DomainValidationError("allocator exceeded the unmet demand")


def _reason(candidate: Candidate, remaining: int, at: Instant) -> SkipReason:
    static = static_skip_reason(candidate, at)
    if static is not None:
        return static
    quote = candidate.quote
    if remaining <= 0:
        return SkipReason.INSUFFICIENT_DEMAND
    if candidate.allocatable_seats <= 0:
        return SkipReason.EXHAUSTED
    if quote is not None and quote.offered_seats > remaining:
        return SkipReason.QUOTE_EXCEEDS_REMAINING_DEMAND
    if quote is not None and quote.offered_seats > candidate.allocatable_seats:
        return SkipReason.INSUFFICIENT_CAPACITY
    return SkipReason.NOT_CHOSEN


def select_offers(
    mission: Mission,
    candidates: tuple[Candidate, ...],
    policy: MobilisationPolicy,
    context: DecisionContext,
    *,
    allocators: Mapping[AlgorithmName, Allocator] = ALLOCATORS,
) -> MobilisationDecision:
    """Allocate seats with the policy's algorithm and return the explained decision.

    Called once per decision with the mission, candidates, policy and context. It rejects
    an allocation that breaks the allocator rules before building anything, then ranks the
    evaluations in allocation order and logs the allocator trace at DEBUG.
    """
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

    allocator = allocators.get(policy.strategy)
    if allocator is None:
        raise DomainValidationError(f"unknown mobilisation strategy: {policy.strategy!r}")

    demand = progress(mission).additional_needed
    result = allocator(candidates, demand, context.recorded_at)
    _validate_allocation(result, candidates, demand, context)

    by_ship = {candidate.ship_id: candidate for candidate in candidates}
    remaining = demand
    evaluations: list[OfferEvaluation] = []
    for rank, (allocation, evaluation_id) in enumerate(
        zip(result.allocations, context.evaluation_ids, strict=True), start=1
    ):
        candidate = by_ship[allocation.ship_id]
        reason = None if allocation.seats else _reason(candidate, remaining, context.recorded_at)
        remaining -= allocation.seats
        evaluations.append(
            OfferEvaluation(
                evaluation_id=evaluation_id,
                rank=rank,
                proposed_seats=allocation.seats,
                selected=allocation.seats > 0,
                reason=None if reason is None else reason.value,
                revision=candidate.revision,
                ship_id=candidate.ship_id,
                quote=candidate.quote,
            )
        )

    for step in result.trace:
        logger.debug(
            "allocator trace step",
            extra={
                "algorithm": step.algorithm,
                "step": step.step,
                "ship_id": step.ship_id,
                "detail": step.detail,
            },
        )

    return MobilisationDecision(
        decision_id=context.decision_id,
        recorded_at=context.recorded_at,
        remaining_demand=remaining,
        evaluations=tuple(evaluations),
        mission_id=mission.mission_id,
        policy_id=policy.policy_id,
        policy_revision=policy.revision,
    )
