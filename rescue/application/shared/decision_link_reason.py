"""Check that a request matches the mobilisation decision it cites.

What: returns the reason code for the first mismatch between the request and the decision, or None.
When called: by open_request, whenever the command names a decision id.
Why: a request that cites a decision must ask for what the decision selected, no more.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from rescue.market.models.quotes import RFQOffer
from rescue.mobilisation.models import MobilisationDecision
from rescue.state import RunState


def decision_link_reason(
    state: RunState,
    decision_id: str | None,
    mission_id: str,
    ship_id: str,
    requested_seats: int,
    revision_id: str | None,
    quote: RFQOffer | None,
) -> str | None:
    """Decision link reason.

    What: checks that a cited decision exists, belongs to the mission and has a selected evaluation for the ship that covers the revision, the seats and the quote; returns the refusal reason or None.
    When called: by open_request when a request names a decision_id.
    Why: a request that cites a decision must match what the decision proposed, otherwise it is refused as unknown_decision or revision_conflict.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    if decision_id is None:
        return None
    decision = next(
        (
            item
            for item in state.decision_index
            if isinstance(item, MobilisationDecision) and item.decision_id == decision_id
        ),
        None,
    )
    if decision is None:
        return "unknown_decision"
    if decision.mission_id != mission_id:
        return "revision_conflict"
    evaluation = next(
        (item for item in decision.evaluations if item.selected and item.ship_id == ship_id),
        None,
    )
    if evaluation is None:
        return "revision_conflict"
    if revision_id is not None and evaluation.revision.revision_id != revision_id:
        return "revision_conflict"
    if requested_seats > evaluation.proposed_seats:
        return "revision_conflict"
    if quote is not None and (
        evaluation.quote is None
        or evaluation.quote.offer_id != quote.offer_id
        or requested_seats != evaluation.proposed_seats
    ):
        return "revision_conflict"
    return None
