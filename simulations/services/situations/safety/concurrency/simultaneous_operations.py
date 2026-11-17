"""Build the concurrency recipe from the actual solver-selected evaluation."""

from simulations.models.concurrent_requests import ConcurrentRequests
from simulations.models.evidence_predicate import EvidencePredicate
from simulations.models.selected_allocation import SelectedAllocation
from simulations.models.situation_id import SituationId
from simulations.models.situation_recipe import SituationRecipe


def recipe(allocation: SelectedAllocation) -> SituationRecipe:
    """Describe two competing copies of a real selected allocation."""
    return SituationRecipe(
        situation_id=SituationId.SIMULTANEOUS_OPERATIONS,
        trigger="Two create-request commands compete for the same selected B2 allocation",
        action=ConcurrentRequests(allocation=allocation, count=2),
        evidence=EvidencePredicate(
            check_name="concurrent_outcomes",
            expected=("applied", "insufficient_capacity"),
        ),
    )
