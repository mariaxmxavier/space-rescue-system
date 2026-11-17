"""A ship's request to confirm seats for one mission.

What: one ask to one ship for N seats, pending until a final outcome closes it.
When called: built by RescueCentral when it mobilises a ship; replaced by the mission rules when
  the ship answers, the request is cancelled, or its deadline passes.
Why: pending seats are tracked per ship, so a refusal or expiry releases exactly that ship's share
  and a closed answer can never change (Constitution II).
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.mission.models._validation import optional_id, optional_instant
from rescue.mission.models.vocabulary.request_outcome import RequestOutcome
from rescue.values import (
    DomainValidationError,
    Id,
    Instant,
    normalize_id,
    normalize_instant,
    normalize_nonnegative_quantity,
    normalize_positive_quantity,
)


def _request_outcome(value: object) -> RequestOutcome:
    """Return the closed outcome named by a member or its string value.

    What: converts the raw outcome and raises the labelled domain error for any other value.
    Why: a request holds only final-state vocabulary, so a typo cannot reach seat accounting.
    """
    try:
        return RequestOutcome(value)
    except ValueError:
        raise DomainValidationError(f"unknown request outcome: {value!r}") from None


def _after_submission(instant: Instant | None, submitted_at: Instant, label: str) -> Instant | None:
    """Return an optional instant unchanged, rejecting one that precedes submission.

    What: passes None through and raises when the instant is earlier than the submission.
    Why: a response or a closure cannot happen before the request existed.
    """
    if instant is not None and instant < submitted_at:
        raise DomainValidationError(f"{label} cannot precede submission")
    return instant


def _check_confirmation(
    outcome: RequestOutcome,
    requested_seats: int,
    confirmed_seats: int,
    response_received_at: Instant | None,
) -> None:
    """Check that confirmed seats and the response receipt agree with the outcome.

    What: applies the request state table to the confirmed count and the receipt time.
    Why: pending seats must never count as transport, and a closed request must match its final state.
    """
    if outcome is RequestOutcome.PENDING and confirmed_seats != 0:
        raise DomainValidationError("pending request cannot confirm seats")
    if outcome is RequestOutcome.ACCEPTED and confirmed_seats != requested_seats:
        raise DomainValidationError("accepted request must confirm all requested seats")
    if outcome is RequestOutcome.PARTIALLY_ACCEPTED and not 0 < confirmed_seats < requested_seats:
        raise DomainValidationError("partial acceptance must confirm a positive subset")
    if outcome in {RequestOutcome.REFUSED, RequestOutcome.CANCELLED, RequestOutcome.EXPIRED}:
        if confirmed_seats != 0:
            raise DomainValidationError(f"{outcome.value} request cannot confirm seats")
    if outcome in {RequestOutcome.CANCELLED, RequestOutcome.EXPIRED}:
        if response_received_at is not None:
            raise DomainValidationError(
                f"{outcome.value} request cannot invent a response receipt time"
            )


@dataclass(frozen=True, slots=True)
class SeatRequest:
    """A ship's request to confirm seats for one mission.

    What: one ask to one ship for N seats, pending until a final outcome closes it.
    When called: built by RescueCentral when it mobilises a ship; replaced by the mission rules
      when the ship answers, the request is cancelled, or its deadline passes.
    Why: pending seats are tracked per ship, so a refusal or expiry releases exactly that ship's
      share and a closed answer can never change (Constitution II).
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """

    request_id: Id
    command_id: Id
    mission_id: Id
    ship_id: Id
    requested_seats: int
    confirmed_seats: int
    outcome: RequestOutcome
    submitted_at: Instant
    response_received_at: Instant | None = None
    response_deadline: Instant | None = None
    closed_at: Instant | None = None
    quote_id: Id | None = None
    revision_id: Id | None = None
    decision_id: Id | None = None

    def __post_init__(self) -> None:
        request_id = normalize_id(self.request_id)
        command_id = normalize_id(self.command_id)
        mission_id = normalize_id(self.mission_id)
        ship_id = normalize_id(self.ship_id)
        requested_seats = normalize_positive_quantity(self.requested_seats)
        confirmed_seats = normalize_nonnegative_quantity(self.confirmed_seats)
        outcome = _request_outcome(self.outcome)
        submitted_at = normalize_instant(self.submitted_at)
        response_received_at = _after_submission(
            optional_instant(self.response_received_at), submitted_at, "response_received_at"
        )
        response_deadline = optional_instant(self.response_deadline)
        closed_at = _after_submission(optional_instant(self.closed_at), submitted_at, "closed_at")
        if response_deadline is not None and response_deadline <= submitted_at:
            raise DomainValidationError("response deadline must follow request submission")
        if (
            response_received_at is not None
            and response_deadline is not None
            and response_received_at >= response_deadline
        ):
            raise DomainValidationError("response received at or after deadline must expire")
        quote_id = optional_id(self.quote_id, "quote id")
        revision_id = optional_id(self.revision_id, "revision id")
        decision_id = optional_id(self.decision_id, "decision id")
        _check_confirmation(outcome, requested_seats, confirmed_seats, response_received_at)

        object.__setattr__(self, "request_id", request_id)
        object.__setattr__(self, "command_id", command_id)
        object.__setattr__(self, "mission_id", mission_id)
        object.__setattr__(self, "ship_id", ship_id)
        object.__setattr__(self, "requested_seats", requested_seats)
        object.__setattr__(self, "confirmed_seats", confirmed_seats)
        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(self, "submitted_at", submitted_at)
        object.__setattr__(self, "response_received_at", response_received_at)
        object.__setattr__(self, "response_deadline", response_deadline)
        object.__setattr__(self, "closed_at", closed_at)
        object.__setattr__(self, "quote_id", quote_id)
        object.__setattr__(self, "revision_id", revision_id)
        object.__setattr__(self, "decision_id", decision_id)
