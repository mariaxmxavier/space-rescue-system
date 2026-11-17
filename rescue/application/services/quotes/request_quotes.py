"""Ask every available ship for a quote for the seats a mission still needs.

What: creates one pending RFQ per available ship with free seats, sized to the outstanding need.
When called: by RescueCentral.request_quotes, which hands the RequestQuotes command to this service.
Why: quotes are solicited from the published availability before any request is created.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.adapters.ports import IdSource, TransactionStore
from rescue.application.contracts import RequestQuotes, Result
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.find_mission import find_mission
from rescue.application.shared.make_result import make_result
from rescue.market.models.availability.rules import latest_availability
from rescue.market.models.inventory.rules import usage
from rescue.market.models.procurement import SeatRFQ
from rescue.mission import rules as mission_rules
from rescue.state import RunState
from rescue.values import DomainValidationError, normalize_instant


def request_quotes(
    command: RequestQuotes, *, store: TransactionStore, id_source: IdSource
) -> Result:
    """Create one pending RFQ per available ship with free seats, sized to the outstanding need of the mission.

    What: Check the mission and deadline, compute the outstanding seats, and for each ship in id order with latest availability and free seats append an RFQ for min(outstanding, free) seats; with no need or no ship, answer an empty applied result.
    When called: RescueCentral.request_quotes in rescue/application/central.py.
    Why: Quotes are solicited from the published availability before any request is created. Asking only ships that can serve avoids holding seats nobody can fill; the id order keeps the outcome reproducible.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def operation(state: RunState):
        """Transaction step of request_quotes.

        What: applies the request_quotes rule to the state it receives and returns the new state with its Result.
        When called: passed to store.transact by request_quotes, which runs it once per call.
        Why: Asking only ships that can serve avoids holding seats nobody can fill; the id order keeps the outcome reproducible.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        try:
            mission = find_mission(state, command.mission_id)
            if mission is None:
                return state, make_result("rejected", reason="unknown_mission")
            now = normalize_instant(command.now)
            deadline = (
                None
                if command.response_deadline is None
                else normalize_instant(command.response_deadline)
            )
            if deadline is not None and deadline <= now:
                return state, make_result("rejected", reason="invalid_input")
            outstanding = mission_rules.progress(mission).additional_needed
            if outstanding == 0:
                return state, make_result("applied", ())
            market = state.market
            created: list[SeatRFQ] = []
            for ship in sorted(market.ships, key=lambda item: item.ship_id):
                latest = latest_availability(market, ship.ship_id)
                if latest is None or not latest.available:
                    continue
                inventory = usage(market, state.missions, ship.ship_id)
                if inventory.shortfall or inventory.free == 0:
                    continue
                requested_seats = min(outstanding, inventory.free)
                if requested_seats <= 0:
                    continue
                rfq = SeatRFQ(
                    rfq_id=id_source.next_id("rfq"),
                    mission_id=mission.mission_id,
                    ship_id=ship.ship_id,
                    availability_id=latest.availability_id,
                    requested_seats=requested_seats,
                    status="pending",
                    sent_at=now,
                    response_deadline=deadline,
                )
                created.append(rfq)
            if not created:
                return state, make_result("applied", ())
            market = replace(market, rfqs=(*market.rfqs, *created))
            return replace(state, market=market), make_result("applied", tuple(created))
        except (DomainValidationError, TypeError) as error:
            return state, make_result("rejected", reason=error_reason_for(error))

    return store.transact(operation)
