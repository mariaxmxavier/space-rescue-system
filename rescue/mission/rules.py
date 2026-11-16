"""Pure mission transitions and seat-accounting rules."""

from __future__ import annotations

from dataclasses import replace

from rescue.mission.models import (
    Mission,
    MissionData,
    MissionProgress,
    RequestTiming,
    RequestHistoryEntry,
    SeatRequest,
)
from rescue.values import DomainValidationError, TransitionContext, normalize_id, normalize_instant

_TERMINAL_OUTCOMES = frozenset(
    {"accepted", "partially_accepted", "refused", "cancelled", "expired"}
)


def register(data: MissionData) -> Mission:
    if not isinstance(data, MissionData):
        raise DomainValidationError("mission registration requires MissionData")
    return Mission(
        mission_id=data.mission_id,
        station_name=data.station_name,
        people_count=data.people_count,
        created_at=data.created_at,
    )


def _account(mission: Mission) -> tuple[int, int]:
    confirmed = sum(request.confirmed_seats for request in mission.requests)
    pending = sum(
        request.requested_seats
        for request in mission.requests
        if request.outcome == "pending"
    )
    if confirmed < 0 or pending < 0 or confirmed + pending > mission.people_count:
        raise DomainValidationError("mission seat accounting invariant violated")
    return confirmed, pending


def _append_history(
    mission: Mission,
    context: TransitionContext,
    *,
    action: str,
    confirmed_delta: int,
    pending_delta: int,
) -> tuple[RequestHistoryEntry, ...]:
    event_id = normalize_id(context.event_id)
    if any(entry.event_id == event_id for entry in mission.history):
        raise DomainValidationError("history event identity must be unique per mission")
    return (
        *mission.history,
        RequestHistoryEntry(
            event_id=event_id,
            mission_sequence=len(mission.history) + 1,
            recorded_at=context.at,
            action=action,
            confirmed_seats_delta=confirmed_delta,
            pending_seats_delta=pending_delta,
            reason=context.reason,
            message_id=context.message_id,
        ),
    )


def add_request(
    mission: Mission, request: SeatRequest, context: TransitionContext
) -> Mission:
    if not isinstance(mission, Mission) or not isinstance(request, SeatRequest):
        raise DomainValidationError("add_request requires Mission and SeatRequest values")
    if not isinstance(context, TransitionContext):
        raise DomainValidationError("add_request requires a TransitionContext")
    if request.mission_id != mission.mission_id:
        raise DomainValidationError("request mission_id does not match its owner")
    if request.outcome != "pending" or request.confirmed_seats != 0:
        raise DomainValidationError("new seat requests must be pending with zero confirmed")
    if request.submitted_at != context.at:
        raise DomainValidationError("request submission time must match transition time")
    if request.submitted_at < mission.created_at:
        raise DomainValidationError("request cannot precede mission registration")
    if any(existing.request_id == request.request_id for existing in mission.requests):
        raise DomainValidationError("request identity must be unique within its mission")
    confirmed, pending = _account(mission)
    if confirmed + pending + request.requested_seats > mission.people_count:
        raise DomainValidationError("request exceeds remaining mission demand")
    history = _append_history(
        mission,
        context,
        action="request_created",
        confirmed_delta=0,
        pending_delta=request.requested_seats,
    )
    updated = replace(mission, requests=(*mission.requests, request), history=history)
    _account(updated)
    return updated


def apply_outcome(
    mission: Mission,
    request_id: str,
    outcome: str,
    confirmed: int,
    context: TransitionContext,
) -> Mission:
    if not isinstance(mission, Mission) or not isinstance(context, TransitionContext):
        raise DomainValidationError("apply_outcome requires Mission and TransitionContext")
    normalized_request_id = normalize_id(request_id)
    matches = [
        (index, request)
        for index, request in enumerate(mission.requests)
        if request.request_id == normalized_request_id
    ]
    if not matches:
        raise DomainValidationError("unknown request")
    index, request = matches[0]
    if request.outcome != "pending":
        raise DomainValidationError("closed requests cannot change outcome")
    if outcome not in _TERMINAL_OUTCOMES:
        raise DomainValidationError("outcome must be a supported terminal request state")
    if type(confirmed) is not int:
        raise DomainValidationError("confirmed seats must be an integer")
    if confirmed < 0 or confirmed > request.requested_seats:
        raise DomainValidationError("confirmation exceeds request quantity")
    if outcome == "accepted" and confirmed != request.requested_seats:
        raise DomainValidationError("accepted outcome must confirm the requested quantity")
    if outcome == "partially_accepted" and not 0 < confirmed < request.requested_seats:
        raise DomainValidationError("partial acceptance must confirm a positive subset")
    if outcome in {"refused", "cancelled", "expired"} and confirmed != 0:
        raise DomainValidationError(f"{outcome} outcome cannot confirm seats")
    if context.at < request.submitted_at:
        raise DomainValidationError("outcome cannot precede request submission")
    if request.response_deadline is not None and outcome in {
        "accepted", "partially_accepted", "refused"
    } and context.at >= request.response_deadline:
        raise DomainValidationError("response is at or after request deadline")

    response_time = (
        None if outcome in {"cancelled", "expired"} else context.at
    )
    updated_request = replace(
        request,
        outcome=outcome,
        confirmed_seats=confirmed,
        response_received_at=response_time,
        closed_at=context.at,
    )
    requests = list(mission.requests)
    requests[index] = updated_request
    history = _append_history(
        mission,
        context,
        action=outcome,
        confirmed_delta=confirmed,
        pending_delta=-request.requested_seats,
    )
    updated = replace(mission, requests=tuple(requests), history=history)
    _account(updated)
    return updated


def progress(mission: Mission) -> MissionProgress:
    if not isinstance(mission, Mission):
        raise DomainValidationError("progress requires a Mission")
    confirmed, pending = _account(mission)
    demand = mission.people_count
    status = (
        "complete"
        if confirmed == demand
        else "awaiting_responses"
        if confirmed + pending == demand
        else "needs_more_help"
    )
    return MissionProgress(
        demand=demand,
        confirmed=confirmed,
        pending=pending,
        unconfirmed=demand - confirmed,
        additional_needed=demand - confirmed - pending,
        status=status,
    )


def timing(request: SeatRequest, now) -> RequestTiming:
    """Project waiting and response time without mutating a request."""
    if not isinstance(request, SeatRequest):
        raise DomainValidationError("timing requires a SeatRequest")
    instant = normalize_instant(now)
    if instant < request.submitted_at:
        raise DomainValidationError("observation time cannot precede request submission")
    if request.response_received_at is None:
        return RequestTiming(
            submitted_at=request.submitted_at,
            response_received_at=None,
            waiting_seconds=instant - request.submitted_at,
            response_elapsed_seconds=None,
        )
    return RequestTiming(
        submitted_at=request.submitted_at,
        response_received_at=request.response_received_at,
        waiting_seconds=0,
        response_elapsed_seconds=request.response_received_at - request.submitted_at,
    )
