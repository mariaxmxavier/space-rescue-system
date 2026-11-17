"""Partial-confirmation and refusal situation ingredients."""

from simulations.models.evidence_predicate import EvidencePredicate
from simulations.models.reply_kind import ReplyKind
from simulations.models.request_selector import RequestSelector
from simulations.models.ship_reply import ShipReply
from simulations.models.situation_id import SituationId
from simulations.models.situation_recipe import SituationRecipe


def recipe(request: RequestSelector, partial_seats: int) -> SituationRecipe:
    """Build the partial-confirmation evidence step for the situation."""
    return SituationRecipe(
        situation_id=SituationId.PARTIAL_AND_REFUSAL,
        trigger="ship partially confirms its selected request",
        action=ShipReply(
            request=request,
            reply=ReplyKind.PARTIAL,
            seats=partial_seats,
            message_label="partial-confirmation",
        ),
        evidence=EvidencePredicate(check_name="application_status", expected="applied"),
    )


def refusal_action(request: RequestSelector) -> ShipReply:
    """Build the companion refusal event, which shares this situation's evidence ID."""
    return ShipReply(
        request=request,
        reply=ReplyKind.REFUSE,
        message_label="refusal",
    )
