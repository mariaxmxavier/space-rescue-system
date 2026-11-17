"""Recipe for a reply received after its request has been cancelled."""

from simulations.models.evidence_predicate import EvidencePredicate
from simulations.models.reply_kind import ReplyKind
from simulations.models.request_selector import RequestSelector
from simulations.models.ship_reply import ShipReply
from simulations.models.situation_id import SituationId
from simulations.models.situation_recipe import SituationRecipe

RECIPE = SituationRecipe(
    situation_id=SituationId.CLOSED_REQUEST_RESPONSE,
    trigger="B replies to its cancelled replacement request",
    action=ShipReply(
        request=RequestSelector(ship_key="B", occurrence=2),
        reply=ReplyKind.CONFIRM,
        seats=2,
        message_label="late-b-cancelled",
    ),
    evidence=EvidencePredicate(check_name="reason", expected="closed_request"),
    dependencies=(SituationId.CANCELLATION,),
)
