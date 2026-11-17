"""Check that a ship can take a new seat request.

What: returns the reason code for the first capacity check the request fails, or None when it fits.
When called: by open_request, for a request that is not tied to a held quote.
Why: a request must fit the ship, its offer revision and the run's free seats before it is stored.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from rescue.application.shared.find_offer_revision import find_offer_revision
from rescue.market.models.availability.rules import latest_availability
from rescue.market.models.inventory.rules import usage
from rescue.mission.models import Mission, RequestOutcome
from rescue.state import RunState
from rescue.values import DomainValidationError


def request_capacity_reason(
    state: RunState,
    mission: Mission,
    ship_id: str,
    quantity: int,
    revision_id: str,
) -> str | None:
    """Request capacity reason.

    What: checks the ship, the offer revision, the latest availability, the ship inventory and the revision capacity against the seats asked; returns the refusal reason or None.
    When called: by open_request when a request is made without a quote.
    Why: a request must not exceed the free seats of the ship or of the offer revision, so refusals are unknown_ship, revision_conflict, unavailable or insufficient_capacity.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    ship = next((item for item in state.market.ships if item.ship_id == ship_id), None)
    if ship is None:
        return "unknown_ship"
    revision = find_offer_revision(state, mission.mission_id, ship_id, revision_id)
    if revision is None:
        return "revision_conflict"
    if not revision.available:
        return "unavailable"
    try:
        latest = latest_availability(state.market, ship_id)
    except DomainValidationError:
        return "unknown_ship"
    if latest is None or not latest.available:
        return "unavailable"
    try:
        inventory = usage(state.market, state.missions, ship_id)
    except DomainValidationError:
        return "invalid_input"
    if inventory.shortfall or quantity > inventory.free:
        return "insufficient_capacity"
    revision_usage = sum(
        request.requested_seats
        if request.outcome == RequestOutcome.PENDING
        else request.confirmed_seats
        for current_mission in state.missions
        for request in current_mission.requests
        if request.revision_id == revision_id
        and request.outcome
        in {
            RequestOutcome.PENDING,
            RequestOutcome.ACCEPTED,
            RequestOutcome.PARTIALLY_ACCEPTED,
        }
    )
    if quantity > max(0, revision.capacity - revision_usage):
        return "insufficient_capacity"
    return None
