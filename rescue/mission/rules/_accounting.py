"""Seat accounting and history append shared by the mission transition rules.

What: the invariant check over confirmed and pending seats, and the history row appended for each
  transition.
Why: every transition checks C, P and D and writes its history the same way, so no rule can apply
  the invariant or the event identity differently from another.
"""

from __future__ import annotations

from rescue.mission.models.mission.mission import Mission
from rescue.mission.models.mission.request_history_entry import RequestHistoryEntry
from rescue.mission.models.vocabulary import HistoryAction, RequestOutcome
from rescue.values import DomainValidationError, TransitionContext, normalize_id


def account(mission: Mission) -> tuple[int, int]:
    """Return the confirmed and pending seat totals after checking the mission invariant.

    What: sums confirmed seats over every request and requested seats over pending requests, then
      requires C >= 0, P >= 0 and C + P <= D.
    Why: a seat count that breaks the invariant would promise seats the mission does not have.
    """
    confirmed = sum(request.confirmed_seats for request in mission.requests)
    pending = sum(
        request.requested_seats
        for request in mission.requests
        if request.outcome == RequestOutcome.PENDING
    )
    if confirmed < 0 or pending < 0 or confirmed + pending > mission.people_count:
        raise DomainValidationError("mission seat accounting invariant violated")
    return confirmed, pending


def append_history(
    mission: Mission,
    context: TransitionContext,
    *,
    action: HistoryAction,
    confirmed_delta: int,
    pending_delta: int,
) -> tuple[RequestHistoryEntry, ...]:
    """Return the mission history with one row for this transition added at the end.

    What: rejects a repeated event identity, then builds the next sequenced entry from the
      transition context and the signed seat deltas.
    Why: each transition leaves exactly one row with a unique event identity, so the history
      explains every change to the seat counts.
    """
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
