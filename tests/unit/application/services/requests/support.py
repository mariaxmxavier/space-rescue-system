"""Run states shared by the request service tests.

What: builds a state with a mission, a ship, its availability and offer, and optionally one pending request.
When called: imported by the create, cancel and expire request tests.
Why: each test starts from one agreed state and stays short.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from dataclasses import replace

from rescue.market.models.availability import ShipAvailability
from rescue.market.models.fleet import Ship
from rescue.market.models.offers import ShipOffer, ShipOfferRevision
from rescue.mission import rules as mission_rules
from rescue.mission.models import Mission, RequestOutcome, SeatRequest
from rescue.values import TransitionContext
from tests.unit.application.services.fakes import empty_state

SUBMITTED = 100
DEADLINE = 200


def state_with_offer():
    base = empty_state()
    market = replace(
        base.market,
        ships=(Ship("SHIP-1", "Rescue One"),),
        availabilities=(ShipAvailability("AVAIL-1", "SHIP-1", 6, 10, True, 1),),
        offers=(
            ShipOffer(
                "OFFER-1",
                "MISSION-1",
                "SHIP-1",
                (ShipOfferRevision("REVISION-1", 1, 6, 10, True, 1),),
            ),
        ),
    )
    return replace(base, market=market, missions=(Mission("MISSION-1", "Station One", 6, 0),))


def state_with_pending_request(deadline=DEADLINE):
    mission = Mission("MISSION-1", "Station One", 6, 0)
    request = SeatRequest(
        request_id="REQUEST-1",
        command_id="COMMAND-1",
        mission_id="MISSION-1",
        ship_id="SHIP-1",
        requested_seats=2,
        confirmed_seats=0,
        outcome=RequestOutcome.PENDING,
        submitted_at=SUBMITTED,
        response_deadline=deadline,
    )
    mission = mission_rules.add_request(
        mission, request, TransitionContext("EVENT-0", SUBMITTED, "request_created")
    )
    return replace(empty_state(), missions=(mission,))
