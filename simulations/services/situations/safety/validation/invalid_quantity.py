"""Recipe for rejecting a confirmation larger than the request."""

from simulations.models.evidence_predicate import EvidencePredicate
from simulations.models.reply_kind import ReplyKind
from simulations.models.request_selector import RequestSelector
from simulations.models.ship_reply import ShipReply
from simulations.models.situation_id import SituationId
from simulations.models.situation_recipe import SituationRecipe

RECIPE = SituationRecipe(
    situation_id=SituationId.INVALID_QUANTITY,
    trigger="C confirms three seats on a two-seat request",
    action=ShipReply(
        request=RequestSelector(ship_key="C", occurrence=3),
        reply=ReplyKind.CONFIRM,
        seats=3,
        message_label="overconfirm-c",
    ),
    evidence=EvidencePredicate(check_name="reason", expected="invalid_input"),
    dependencies=(SituationId.EXPIRATION,),
)
