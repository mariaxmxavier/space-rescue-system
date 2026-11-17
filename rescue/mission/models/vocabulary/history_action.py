"""Closed vocabulary of the actions a mission's history can record.

What: the six action labels stored on each history entry, one per request event.
When called: stored by RequestHistoryEntry; add_request records REQUEST_CREATED and apply_outcome
  records the closing outcome as the action.
Why: a closed set keeps the mission history readable and stops free-text actions from drifting.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from __future__ import annotations

from enum import StrEnum


class HistoryAction(StrEnum):
    """The event a single history entry records against a mission.

    What: one value per event that changes a mission's confirmed or pending seats.
    When called: assigned when RequestHistoryEntry is built by the mission rules.
    Why: pending is a live state, not an event, so it is deliberately absent from this set.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """

    REQUEST_CREATED = "request_created"
    ACCEPTED = "accepted"
    PARTIALLY_ACCEPTED = "partially_accepted"
    REFUSED = "refused"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
