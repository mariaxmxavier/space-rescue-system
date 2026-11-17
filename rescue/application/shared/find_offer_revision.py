"""Find one revision of a ship's offer to a mission.

What: returns the revision with this id from the ship's offer to the mission, or None.
When called: by publish_offer and open_request.
Why: pinning a request to a revision needs the same lookup wherever offers are read.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from rescue.state import RunState


def find_offer_revision(state: RunState, mission_id: str, ship_id: str, revision_id: str):
    """Find offer revision.

    What: returns the offer revision with this id for the mission and ship, or None.
    When called: by open_request and request_capacity_reason.
    Why: a request must target a revision that the ship really published for the mission.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    for offer in state.market.offers:
        if offer.mission_id == mission_id and offer.ship_id == ship_id:
            for revision in offer.revisions:
                if revision.revision_id == revision_id:
                    return revision
    return None
