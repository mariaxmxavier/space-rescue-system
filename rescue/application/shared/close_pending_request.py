"""Close one pending seat request with a final outcome.

What: checks mission, request and pending status, runs the optional guard, then applies the outcome.
When called: by cancel_request (event_first=True) and by expire_request (event_first=False, with a
  guard that waits for the deadline).
Why: both closures share one order of checks and leave the state unchanged on any refusal, while
  each keeps its original event id draw order.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from collections.abc import Callable

from rescue.adapters.ports import IdSource
from rescue.application.contracts import Result
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.find_mission import find_mission
from rescue.application.shared.make_result import make_result
from rescue.application.shared.replace_mission import replace_mission
from rescue.mission import rules as mission_rules
from rescue.mission.models import RequestOutcome, SeatRequest
from rescue.state import RunState
from rescue.values import DomainValidationError, TransitionContext, normalize_instant


def close_pending_request(
    state: RunState,
    mission_id: str,
    request_id: str,
    outcome: RequestOutcome | str,
    at,
    reason: str,
    *,
    id_source: IdSource,
    event_first: bool,
    guard: Callable[[SeatRequest, object], Result | None] | None = None,
) -> tuple[RunState, Result]:
    """Close pending request.

    What: finds the mission and the request, ignores a request that is not pending, runs the optional guard, applies the outcome through mission_rules.apply_outcome and returns the new state with the result.
    When called: by cancel_request (event_first=True) and expire_request (event_first=False, with a deadline guard), run by RescueCentral.cancel_request and RescueCentral.expire_request.
    Why: cancel and expire share one order of checks and leave the state unchanged on any refusal, while each keeps its own event id draw order.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    mission = find_mission(state, mission_id)
    if mission is None:
        return state, make_result("rejected", reason="unknown_mission")
    request = next((item for item in mission.requests if item.request_id == request_id), None)
    if request is None:
        return state, make_result("rejected", reason="unknown_request")
    if request.outcome != RequestOutcome.PENDING:
        return state, make_result("ignored", request, "closed_request")
    try:
        event_id = id_source.next_id("event") if event_first else None
        instant = normalize_instant(at)
        if guard is not None:
            rejection = guard(request, instant)
            if rejection is not None:
                return state, rejection
        if event_id is None:
            event_id = id_source.next_id("event")
        updated = mission_rules.apply_outcome(
            mission,
            request.request_id,
            outcome,
            0,
            TransitionContext(event_id, instant, reason),
        )
        updated_state = replace_mission(state, updated)
        return updated_state, make_result(
            "applied",
            next(item for item in updated.requests if item.request_id == request.request_id),
        )
    except (DomainValidationError, TypeError) as error:
        return state, make_result("rejected", reason=error_reason_for(error))
