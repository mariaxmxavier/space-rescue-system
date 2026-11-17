"""Record a ship's new pending seat request against a mission.

What: the transition that adds one pending request to a mission and appends its creation row to
  the history, after checking the request against the mission and the transition.
When called: applied by the central application when it mobilises a ship for a mission.
Why: a new request must belong to its mission, arrive at the transition time and fit the remaining
  demand, otherwise the mission would promise seats it does not have (Constitution I).
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.mission.models.mission.mission import Mission
from rescue.mission.models.mission.seat_request import SeatRequest
from rescue.mission.models.vocabulary.history_action import HistoryAction
from rescue.mission.models.vocabulary.request_outcome import RequestOutcome
from rescue.mission.rules._accounting import account, append_history
from rescue.values import DomainValidationError, TransitionContext


def add_request(mission: Mission, request: SeatRequest, context: TransitionContext) -> Mission:
    """Return the mission with the pending request appended and its creation recorded in history.

    What: checks the request against the mission and the transition, then returns a new Mission
      whose requests and history each gain one entry.
    When called: by the central application when a ship is asked for seats, before it answers.
    Why: the mission is never changed in place, and a request that breaks identity, timing or
      demand is rejected before any tuple is rebuilt.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """
    if not isinstance(mission, Mission) or not isinstance(request, SeatRequest):
        raise DomainValidationError("add_request requires Mission and SeatRequest values")
    if not isinstance(context, TransitionContext):
        raise DomainValidationError("add_request requires a TransitionContext")
    if request.mission_id != mission.mission_id:
        raise DomainValidationError("request mission_id does not match its owner")
    if request.outcome != RequestOutcome.PENDING or request.confirmed_seats != 0:
        raise DomainValidationError("new seat requests must be pending with zero confirmed")
    if request.submitted_at != context.at:
        raise DomainValidationError("request submission time must match transition time")
    if request.submitted_at < mission.created_at:
        raise DomainValidationError("request cannot precede mission registration")
    if any(existing.request_id == request.request_id for existing in mission.requests):
        raise DomainValidationError("request identity must be unique within its mission")
    confirmed, pending = account(mission)
    if confirmed + pending + request.requested_seats > mission.people_count:
        raise DomainValidationError("request exceeds remaining mission demand")
    history = append_history(
        mission,
        context,
        action=HistoryAction.REQUEST_CREATED,
        confirmed_delta=0,
        pending_delta=request.requested_seats,
    )
    updated = replace(mission, requests=(*mission.requests, request), history=history)
    account(updated)
    return updated
