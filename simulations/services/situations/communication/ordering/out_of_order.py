"""Recipe for observing a gap followed by an obsolete sequence delivery."""

from decimal import Decimal

from simulations.models.evidence_predicate import EvidencePredicate
from simulations.models.reply_kind import ReplyKind
from simulations.models.request_selector import RequestSelector
from simulations.models.ship_reply import ShipReply
from simulations.models.situation_id import SituationId
from simulations.models.situation_recipe import SituationRecipe


def out_of_order_recipe(
    request: RequestSelector,
    *,
    seats: int,
    sent_at: Decimal,
    message_label: str = "obsolete-sequence-response",
    sequence: int,
) -> SituationRecipe:
    """Describe delivery of an earlier sequence after a later sequence opened a gap."""
    return SituationRecipe(
        situation_id=SituationId.OUT_OF_ORDER,
        trigger="An earlier session sequence arrives after a later sequence was recorded.",
        action=ShipReply(
            request=request,
            reply=ReplyKind.CONFIRM,
            seats=seats,
            message_label=message_label,
            sent_at=sent_at,
            sequence=sequence,
        ),
        evidence=EvidencePredicate(
            check_name="session_gap_and_obsolete_sequence",
            expected=("gap", "duplicate_sequence"),
        ),
    )
