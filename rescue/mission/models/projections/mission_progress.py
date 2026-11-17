"""Seat progress of one mission, read from its accounting.

What: the demand, confirmed seats and pending seats of a mission, with the seats still unconfirmed
  and still needed, and the progress status those counts imply.
When called: returned by the progress rule to the application, which shows how many seats still
  need a ship.
Why: the status must agree with the counts, so a read can never report pending seats as complete
  (Constitution I).
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.mission.models.vocabulary import ProgressStatus
from rescue.values import (
    DomainValidationError,
    normalize_nonnegative_quantity,
    normalize_positive_quantity,
)


def _as_progress_status(value: object) -> ProgressStatus:
    """What: converts a ProgressStatus or its wire string into the member, or raises.
    Why: callers may still pass the wire string, and an unknown value must fail as a domain error.
    """
    try:
        return ProgressStatus(value)
    except ValueError as error:
        raise DomainValidationError(f"invalid mission progress status: {value!r}") from error


def _derive_status(demand: int, confirmed: int, pending: int) -> ProgressStatus:
    """What: the status implied by the seat counts, complete before awaiting responses.
    Why: a stored status that disagrees with the counts would let a mission look finished early.
    """
    if confirmed == demand:
        return ProgressStatus.COMPLETE
    if confirmed + pending == demand:
        return ProgressStatus.AWAITING_RESPONSES
    return ProgressStatus.NEEDS_MORE_HELP


@dataclass(frozen=True, slots=True)
class MissionProgress:
    """Read-only accounting snapshot of a mission's seats.

    What: the demand, the confirmed and pending seats, the unconfirmed seats (demand minus
      confirmed) and the additional seats still needed (demand minus confirmed minus pending),
      with the status that the counts imply.
    When called: built by the progress rule each time a mission's progress is read; never stored
      on the mission.
    Why: the counts are checked against each other on construction, so a snapshot can only
      describe a state that the mission's requests can reach (Constitution I).
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """

    demand: int
    confirmed: int
    pending: int
    unconfirmed: int
    additional_needed: int
    status: ProgressStatus

    def __post_init__(self) -> None:
        demand = normalize_positive_quantity(self.demand)
        confirmed = normalize_nonnegative_quantity(self.confirmed)
        pending = normalize_nonnegative_quantity(self.pending)
        unconfirmed = normalize_nonnegative_quantity(self.unconfirmed)
        additional_needed = normalize_nonnegative_quantity(self.additional_needed)
        if confirmed + pending > demand:
            raise DomainValidationError("confirmed and pending seats exceed mission demand")
        if unconfirmed != demand - confirmed:
            raise DomainValidationError("unconfirmed seats do not match mission accounting")
        if additional_needed != demand - confirmed - pending:
            raise DomainValidationError("additional demand does not match mission accounting")
        status = _as_progress_status(self.status)
        if status != _derive_status(demand, confirmed, pending):
            raise DomainValidationError(f"invalid mission progress status: {self.status!r}")
        object.__setattr__(self, "demand", demand)
        object.__setattr__(self, "confirmed", confirmed)
        object.__setattr__(self, "pending", pending)
        object.__setattr__(self, "unconfirmed", unconfirmed)
        object.__setattr__(self, "additional_needed", additional_needed)
        object.__setattr__(self, "status", status)
