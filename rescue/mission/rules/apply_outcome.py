"""Closes a pending seat request with its ship's final answer.

What: the transition that applies a ship's final outcome to one pending request in a mission.
When called: by RescueCentral when a ship answers, when a request is cancelled, and when its
  deadline passes; the tests call it with a Mission and a TransitionContext, as RescueCentral does.
Why: a closed request is final and releases its unconfirmed share, so the mission seat invariant
  holds after every answer.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.mission.models.mission.mission import Mission
from rescue.mission.models.mission.seat_request import SeatRequest
from rescue.mission.models.vocabulary.history_action import HistoryAction
from rescue.mission.models.vocabulary.request_outcome import RequestOutcome
from rescue.mission.rules._accounting import account, append_history
from rescue.values import DomainValidationError, Instant, TransitionContext, normalize_id


def apply_outcome(
    mission: Mission,
    request_id: str,
    outcome: RequestOutcome | str,
    confirmed: int,
    context: TransitionContext,
) -> Mission:
    """Return the mission with one pending request closed by its final outcome.

    What: finds the named request, checks the outcome, the confirmed seats and the answer time
      against the request, then closes it and appends one history row.
    When called: by RescueCentral when a ship answers, when a request is cancelled, and when its
      deadline passes.
    Why: a closed request is final, and each closure releases its unconfirmed share, so the seat
      invariant holds after every answer.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """
    if not isinstance(mission, Mission) or not isinstance(context, TransitionContext):
        raise DomainValidationError("apply_outcome requires Mission and TransitionContext")
    index, request = _pending_request(mission, normalize_id(request_id))
    final = _final_outcome(outcome)
    _check_confirmed(final, request.requested_seats, confirmed)
    _check_answer_time(request, final, context.at)
    without_receipt = final in {RequestOutcome.CANCELLED, RequestOutcome.EXPIRED}
    closed = replace(
        request,
        outcome=final,
        confirmed_seats=confirmed,
        response_received_at=None if without_receipt else context.at,
        closed_at=context.at,
    )
    updated = replace(
        mission,
        requests=(*mission.requests[:index], closed, *mission.requests[index + 1 :]),
        history=append_history(
            mission,
            context,
            action=HistoryAction(final.value),
            confirmed_delta=confirmed,
            pending_delta=-request.requested_seats,
        ),
    )
    account(updated)
    return updated


def _pending_request(mission: Mission, request_id: str) -> tuple[int, SeatRequest]:
    """Return the position and value of the named request, which must still be pending.

    What: looks up the request by id, then rejects it when it is unknown or already closed.
    Why: a closed request is final, so an answer can only close a pending one.
    """
    matches = tuple(
        (index, request)
        for index, request in enumerate(mission.requests)
        if request.request_id == request_id
    )
    if not matches:
        raise DomainValidationError("unknown request")
    index, request = matches[0]
    if request.outcome is not RequestOutcome.PENDING:
        raise DomainValidationError("closed requests cannot change outcome")
    return index, request


def _final_outcome(outcome: RequestOutcome | str) -> RequestOutcome:
    """Return the final outcome named by a member or its string value.

    What: accepts one of the five final outcomes as a member or as its string value and rejects
      anything else.
    Why: a request may only close with a final state, so pending and unknown names never reach
      the seat accounting.
    """
    if outcome not in RequestOutcome.final():
        raise DomainValidationError("outcome must be a supported terminal request state")
    return RequestOutcome(outcome)


def _check_confirmed(outcome: RequestOutcome, requested: int, confirmed: object) -> None:
    """Check the confirmed seat count against the requested quantity and the outcome.

    What: requires an integer between zero and the requested quantity, then the count the outcome
      allows.
    Why: a ship cannot confirm more seats than it was asked for, and a closed request must agree
      with its outcome.
    """
    if type(confirmed) is not int:
        raise DomainValidationError("confirmed seats must be an integer")
    if confirmed < 0 or confirmed > requested:
        raise DomainValidationError("confirmation exceeds request quantity")
    if outcome is RequestOutcome.ACCEPTED and confirmed != requested:
        raise DomainValidationError("accepted outcome must confirm the requested quantity")
    if outcome is RequestOutcome.PARTIALLY_ACCEPTED and not 0 < confirmed < requested:
        raise DomainValidationError("partial acceptance must confirm a positive subset")
    cannot_confirm = {RequestOutcome.REFUSED, RequestOutcome.CANCELLED, RequestOutcome.EXPIRED}
    if outcome in cannot_confirm and confirmed != 0:
        raise DomainValidationError(f"{outcome.value} outcome cannot confirm seats")


def _check_answer_time(request: SeatRequest, outcome: RequestOutcome, at: Instant) -> None:
    """Check that the answer comes after submission and, for a ship's answer, before its deadline.

    What: rejects an instant before submission, and an accepted, partial or refused answer at or
      after the response deadline.
    Why: a ship cannot answer before it was asked, and a late answer must not count, while
      cancellation and expiry close the request without an answer and are not checked against the
      deadline.
    """
    if at < request.submitted_at:
        raise DomainValidationError("outcome cannot precede request submission")
    deadline = request.response_deadline
    answered_by_ship = outcome in {
        RequestOutcome.ACCEPTED,
        RequestOutcome.PARTIALLY_ACCEPTED,
        RequestOutcome.REFUSED,
    }
    if deadline is not None and answered_by_ship and at >= deadline:
        raise DomainValidationError("response is at or after request deadline")
