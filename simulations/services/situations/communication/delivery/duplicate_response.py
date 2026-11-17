"""Recipe for replaying an accepted ship response after mission completion."""

from simulations.models.evidence_predicate import EvidencePredicate
from simulations.models.reply_kind import ReplyKind
from simulations.models.request_selector import RequestSelector
from simulations.models.ship_reply import ShipReply
from simulations.models.situation_id import SituationId
from simulations.models.situation_recipe import SituationRecipe


def duplicate_response_recipe(
    request: RequestSelector,
    *,
    accepted_seats: int,
    message_label: str = "accepted-response-replay",
    original_message_label: str = "accepted-response",
    original_sequence: int,
) -> SituationRecipe:
    """Describe the same accepted message arriving again under a new delivery attempt."""
    return SituationRecipe(
        situation_id=SituationId.DUPLICATE_RESPONSE,
        trigger="An accepted message is replayed with the same identity and payload.",
        action=ShipReply(
            request=request,
            reply=ReplyKind.CONFIRM,
            seats=accepted_seats,
            message_label=message_label,
            delivery_attempt=2,
            replay_of=original_message_label,
            sequence=original_sequence,
        ),
        evidence=EvidencePredicate(check_name="message_replay", expected=True),
    )
