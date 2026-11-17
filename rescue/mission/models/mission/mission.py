"""Mission aggregate root: one rescue job's demand, its seat requests and its history.

What: the mission record that holds the station, the fixed demand D, and the tuples of seat
  requests and history entries the mission owns.
When called: built by the register rule from the registration input, and rebuilt with new tuples
  by add_request and apply_outcome when a transition is applied.
Why: the mission is the one owner of its requests and history, so every transition returns a new
  snapshot and an invalid input never leaves a partly updated mission behind (Constitution III).
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.mission.models._validation import normalize_name
from rescue.mission.models.mission.request_history_entry import RequestHistoryEntry
from rescue.mission.models.mission.seat_request import SeatRequest
from rescue.values import (
    DomainValidationError,
    Id,
    Instant,
    immutable_tuple,
    normalize_id,
    normalize_instant,
    normalize_positive_quantity,
)


@dataclass(frozen=True, slots=True)
class Mission:
    """Immutable mission aggregate with fixed demand and tuple-owned requests and history.

    What: identity, station name, demand people_count, creation instant, and the requests and
      history tuples the mission owns.
    When called: returned by the register rule and by every transition rule that changes seats,
      and read by the progress and timing rules.
    Why: owning both tuples in one frozen value lets the accounting rule check C, P and D from a
      single snapshot (Constitution I).
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """

    mission_id: Id
    station_name: str
    people_count: int
    created_at: Instant
    requests: tuple[SeatRequest, ...] = ()
    history: tuple[RequestHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "mission_id", normalize_id(self.mission_id))
        object.__setattr__(self, "station_name", normalize_name(self.station_name, "station name"))
        object.__setattr__(self, "people_count", normalize_positive_quantity(self.people_count))
        object.__setattr__(self, "created_at", normalize_instant(self.created_at))
        requests = immutable_tuple(self.requests)
        history = immutable_tuple(self.history)
        if any(not isinstance(request, SeatRequest) for request in requests):
            raise DomainValidationError("mission requests must be SeatRequest values")
        if any(not isinstance(entry, RequestHistoryEntry) for entry in history):
            raise DomainValidationError("mission history must contain RequestHistoryEntry values")
        object.__setattr__(self, "requests", requests)
        object.__setattr__(self, "history", history)
