"""Full-confirmation situation recipe."""

from simulations.models.evidence_predicate import EvidencePredicate
from simulations.models.reply_kind import ReplyKind
from simulations.models.request_selector import RequestSelector
from simulations.models.ship_reply import ShipReply
from simulations.models.situation_id import SituationId
from simulations.models.situation_recipe import SituationRecipe


def recipe(request: RequestSelector, seats: int) -> SituationRecipe:
    """Build evidence for a solver-created request fully confirmed by its ship."""
    return SituationRecipe(
        situation_id=SituationId.FULL_CONFIRMATION,
        trigger="ship fully confirms its selected request",
        action=ShipReply(
            request=request,
            reply=ReplyKind.CONFIRM,
            seats=seats,
            message_label="full-confirmation",
        ),
        evidence=EvidencePredicate(check_name="application_status", expected="applied"),
    )
