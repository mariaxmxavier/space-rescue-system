"""One recorded change to a mission's seat counts.

What: an immutable history row naming the action and the signed seat deltas it caused.
When called: built by the mission rules when a request is added or closed, then appended to
  Mission.history.
Why: each seat change leaves one row, so the mission's accounting can be explained after the fact.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.mission.models._validation import (
    normalize_name,
    optional_id,
    signed_quantity,
)
from rescue.mission.models.vocabulary.history_action import HistoryAction
from rescue.values import (
    DomainValidationError,
    Id,
    Instant,
    normalize_id,
    normalize_instant,
    normalize_positive_quantity,
)


def _history_action(value: str) -> HistoryAction:
    """Return the closed history action with this value, or raise a domain error.

    What: looks up a HistoryAction by its string value and passes members through unchanged.
    Why: an action outside the closed set would be stored as free text and drift from the vocabulary.
    """
    try:
        return HistoryAction(value)
    except ValueError as error:
        raise DomainValidationError(f"unknown history action: {value!r}") from error


@dataclass(frozen=True, slots=True)
class RequestHistoryEntry:
    """One applied request creation or closing transition in mission history.

    What: records the event, its action, the confirmed and pending seat deltas, and why it happened.
    When called: created by the mission rules when a request is added or closed by an outcome.
    Why: deltas stay signed, so a confirmation and a release read the same way in the history.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """

    event_id: Id
    mission_sequence: int
    recorded_at: Instant
    action: HistoryAction
    confirmed_seats_delta: int
    pending_seats_delta: int
    reason: str
    message_id: Id | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", normalize_id(self.event_id))
        object.__setattr__(
            self, "mission_sequence", normalize_positive_quantity(self.mission_sequence)
        )
        object.__setattr__(self, "recorded_at", normalize_instant(self.recorded_at))
        object.__setattr__(
            self, "action", _history_action(normalize_name(self.action, "history action"))
        )
        object.__setattr__(
            self,
            "confirmed_seats_delta",
            signed_quantity(self.confirmed_seats_delta, "confirmed seats delta"),
        )
        object.__setattr__(
            self,
            "pending_seats_delta",
            signed_quantity(self.pending_seats_delta, "pending seats delta"),
        )
        object.__setattr__(self, "reason", normalize_name(self.reason, "history reason"))
        object.__setattr__(self, "message_id", optional_id(self.message_id, "message id"))
