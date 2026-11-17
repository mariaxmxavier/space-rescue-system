"""Cancellation situation recipe."""

from simulations.models.close_kind import CloseKind
from simulations.models.close_request import CloseRequest
from simulations.models.evidence_predicate import EvidencePredicate
from simulations.models.request_selector import RequestSelector
from simulations.models.situation_id import SituationId
from simulations.models.situation_recipe import SituationRecipe


def recipe(request: RequestSelector) -> SituationRecipe:
    """Build evidence for explicit cancellation of a bound request."""
    return SituationRecipe(
        situation_id=SituationId.CANCELLATION,
        trigger="pending request is explicitly cancelled",
        action=CloseRequest(request=request, close_as=CloseKind.CANCEL),
        evidence=EvidencePredicate(check_name="application_status", expected="applied"),
    )
