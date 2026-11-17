"""Registration input for one rescue mission.

What: the station, demand and creation time a mission is registered with.
When called: built by the central application and passed to register, which starts the mission.
Why: demand is fixed at registration, so later rules read one positive, normalised seat count.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.mission.models._validation import normalize_name
from rescue.values import Id, Instant, normalize_id, normalize_instant, normalize_positive_quantity


@dataclass(frozen=True, slots=True)
class MissionData:
    """Registration input; demand is a positive, fixed mission property.

    What: the four facts that identify a mission and fix its demand D.
    When called: passed to register, which turns it into a Mission with no requests or history.
    Why: demand is set once, so seat accounting never reconciles a changing demand (Constitution I).
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """

    mission_id: Id
    station_name: str
    people_count: int
    created_at: Instant

    def __post_init__(self) -> None:
        """Validate each field in order and store its normalised form.

        What: checks the identifier, station name, demand and creation instant.
        Why: an invalid registration fails here, before any rule can read it.
        """
        object.__setattr__(self, "mission_id", normalize_id(self.mission_id))
        object.__setattr__(self, "station_name", normalize_name(self.station_name, "station name"))
        object.__setattr__(self, "people_count", normalize_positive_quantity(self.people_count))
        object.__setattr__(self, "created_at", normalize_instant(self.created_at))
