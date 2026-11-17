"""Recipe for a response delivered after its request deadline."""

from decimal import Decimal

from simulations.models.evidence_predicate import EvidencePredicate
from simulations.models.reply_kind import ReplyKind
from simulations.models.request_selector import RequestSelector
from simulations.models.ship_reply import ShipReply
from simulations.models.situation_id import SituationId
from simulations.models.situation_recipe import SituationRecipe


def delayed_response_recipe(
    request: RequestSelector,
    *,
    seats: int,
    sent_at: Decimal,
    message_label: str = "late-response-retry",
    original_message_label: str = "delayed-response-original",
    sequence: int,
) -> SituationRecipe:
    """Describe a retry whose original send time precedes the request deadline."""
    return SituationRecipe(
        situation_id=SituationId.DELAYED_RESPONSE,
        trigger="A response sent before the deadline is received after the request expires.",
        action=ShipReply(
            request=request,
            reply=ReplyKind.CONFIRM,
            seats=seats,
            message_label=message_label,
            delivery_attempt=2,
            sent_at=sent_at,
            replay_of=original_message_label,
            sequence=sequence,
        ),
        evidence=EvidencePredicate(check_name="delivery_reason", expected="late"),
    )
