"""Run states for the quote service tests.

What: builds a state with a mission, one available ship, an RFQ and, optionally, a held quote.
When called: imported by the quote service tests.
Why: each test starts from the same small market and changes only what it checks.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from dataclasses import replace

from rescue.market.models.availability import ShipAvailability
from rescue.market.models.availability.rules import publish_availability
from rescue.market.models.fleet import Ship
from rescue.market.models.procurement import SeatRFQ
from rescue.market.models.quotes import RFQOffer
from rescue.mission import rules as mission_rules
from rescue.mission.models import MissionData
from rescue.state import RunState
from tests.unit.application.services.fakes import empty_state


def market_state(people_count=5, available=True) -> RunState:
    state = empty_state()
    mission = mission_rules.register(MissionData("MISSION-1", "Station One", people_count, 0))
    market = replace(state.market, ships=(Ship("SHIP-1", "Rescue One"),))
    market = publish_availability(
        market, ShipAvailability("AVAIL-1", "SHIP-1", 6, 10, available, 0)
    )
    return replace(state, market=market, missions=(mission,))


def rfq(response_deadline=None, status="pending") -> SeatRFQ:
    return SeatRFQ("RFQ-1", "MISSION-1", "SHIP-1", "AVAIL-1", 3, status, 1, response_deadline)


def quote(expires_at=30, seats=3) -> RFQOffer:
    return RFQOffer("QUOTE-1", "RFQ-1", seats, 10, expires_at, 1)


def with_rfq(state: RunState, **kwargs) -> RunState:
    return replace(state, market=replace(state.market, rfqs=(rfq(**kwargs),)))


def with_held_quote(state: RunState, expires_at=30, seats=3) -> RunState:
    state = with_rfq(state)
    market = replace(state.market, quotes=(quote(expires_at, seats),))
    return replace(state, market=market)
