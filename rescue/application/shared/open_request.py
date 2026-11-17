"""Open a pending seat request on a mission, directly or from a held quote.

What: validates the command, runs the decision, capacity and quote checks, then adds the request,
  transfers the quote when there is one, and records the command.
When called: by create_request, and by accept_quote with the held quote.
Why: a request and a quote acceptance share one set of checks, one id draw and one stored command.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.adapters.ports import IdSource
from rescue.application.contracts import Result
from rescue.application.shared.append_command import append_command
from rescue.application.shared.command_entry import command_entry
from rescue.application.shared.decision_link_reason import decision_link_reason
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.find_mission import find_mission
from rescue.application.shared.find_offer_revision import find_offer_revision
from rescue.application.shared.find_rfq import find_rfq
from rescue.application.shared.make_result import make_result
from rescue.application.shared.replace_mission import replace_mission
from rescue.application.shared.request_capacity_reason import request_capacity_reason
from rescue.market.models.quotes import RFQOffer
from rescue.market.models.quotes.rules import transfer_quote
from rescue.mission import rules as mission_rules
from rescue.mission.models import RequestOutcome, SeatRequest
from rescue.state import RunState
from rescue.values import (
    DomainValidationError,
    TransitionContext,
    normalize_id,
    normalize_instant,
    normalize_positive_quantity,
)


def open_request(
    state: RunState,
    *,
    id_source: IdSource,
    command_id: str,
    mission_id: str,
    ship_id: str,
    requested_seats: int,
    revision_id: str,
    now,
    response_deadline,
    decision_id: str | None,
    quote: RFQOffer | None = None,
) -> tuple[RunState, Result]:
    """Open request.

    What: normalises the command, replays or refuses a repeated command id, checks mission, decision link, capacity or quote and deadline, then adds a pending SeatRequest, transfers the quote when there is one and records the command.
    When called: by create_request and accept_quote, run by RescueCentral.create_request and RescueCentral.accept_quote.
    Why: creating a request directly and accepting a quote share one set of checks, and any refusal leaves the state unchanged.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    try:
        command_id = normalize_id(command_id)
        mission_id = normalize_id(mission_id)
        ship_id = normalize_id(ship_id)
        requested_seats = normalize_positive_quantity(requested_seats)
        revision_id = normalize_id(revision_id) if revision_id is not None else None
        instant = normalize_instant(now)
        deadline = None if response_deadline is None else normalize_instant(response_deadline)
        decision_id = None if decision_id is None else normalize_id(decision_id)
        payload = (
            mission_id,
            ship_id,
            requested_seats,
            None if quote is None else quote.offer_id,
            revision_id,
            decision_id,
            deadline,
        )
        existing_command = command_entry(state, command_id)
        if existing_command is not None:
            if existing_command[2] == "create_request" and existing_command[3] == payload:
                return state, make_result("replayed", existing_command[4])
            return state, make_result("rejected", reason="identity_conflict")

        mission = find_mission(state, mission_id)
        if mission is None:
            return state, make_result("rejected", reason="unknown_mission")
        decision_reason = decision_link_reason(
            state,
            decision_id,
            mission_id,
            ship_id,
            requested_seats,
            revision_id,
            quote,
        )
        if decision_reason is not None:
            return state, make_result("rejected", reason=decision_reason)
        if quote is None:
            if revision_id is None:
                return state, make_result("rejected", reason="revision_conflict")
            capacity_reason = request_capacity_reason(
                state, mission, ship_id, requested_seats, revision_id
            )
            if capacity_reason is not None:
                return state, make_result("rejected", reason=capacity_reason)
        else:
            rfq = find_rfq(state, quote.rfq_id)
            if rfq is None or rfq.mission_id != mission_id or rfq.ship_id != ship_id:
                return state, make_result("rejected", reason="identity_conflict")
            if quote.status != "held":
                return state, make_result(
                    "rejected",
                    reason="expired_quote" if quote.status == "expired" else "identity_conflict",
                )
            if quote.expires_at <= instant:
                return state, make_result("rejected", reason="expired_quote")
            if requested_seats != quote.offered_seats:
                return state, make_result("rejected", reason="identity_conflict")
            if (
                revision_id is not None
                and find_offer_revision(state, mission_id, ship_id, revision_id) is None
            ):
                return state, make_result("rejected", reason="revision_conflict")
        if deadline is not None and deadline <= instant:
            return state, make_result("rejected", reason="invalid_input")

        request = SeatRequest(
            request_id=id_source.next_id("request"),
            command_id=command_id,
            mission_id=mission_id,
            ship_id=ship_id,
            requested_seats=requested_seats,
            confirmed_seats=0,
            outcome=RequestOutcome.PENDING,
            submitted_at=instant,
            response_deadline=deadline,
            quote_id=None if quote is None else quote.offer_id,
            revision_id=revision_id,
            decision_id=decision_id,
        )
        context = TransitionContext(
            event_id=id_source.next_id("event"),
            at=instant,
            reason="quote_accepted" if quote is not None else "request_created",
        )
        updated_mission = mission_rules.add_request(mission, request, context)
        updated_state = replace_mission(state, updated_mission)
        if quote is not None:
            updated_market = transfer_quote(
                updated_state.market, quote.offer_id, request.request_id, instant
            )
            updated_state = replace(updated_state, market=updated_market)
        updated_state = append_command(
            updated_state, command_id, "create_request", payload, request
        )
        return updated_state, make_result("applied", request)
    except (DomainValidationError, TypeError) as error:
        return state, make_result("rejected", reason=error_reason_for(error))
