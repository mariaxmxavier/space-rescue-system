"""Registration rule that opens a mission with its fixed demand.

What: turns one MissionData registration into a Mission that owns no requests and no history.
When called: called by the central application when a rescue job is opened, before any seat
  request is added to it.
Why: every later transition starts from a registered mission, so this is the only place a mission
  is created and it cannot arrive already carrying requests or history.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from __future__ import annotations

from rescue.mission.models.mission.mission import Mission
from rescue.mission.models.mission.mission_data import MissionData
from rescue.values import DomainValidationError


def register(data: MissionData) -> Mission:
    """Open a mission from its registration input, with no requests and no history.

    What: rejects any argument that is not MissionData, then copies its identity, station, demand
      and creation instant into a new Mission.
    When called: by the central application for each new rescue job, and by the mission rules
      tests as the starting point of every transition.
    Why: copying only the four registration fields keeps the demand fixed from the first moment,
      and rejecting other inputs stops a caller from registering a mission without a validated
      registration.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """
    if not isinstance(data, MissionData):
        raise DomainValidationError("mission registration requires MissionData")
    return Mission(
        mission_id=data.mission_id,
        station_name=data.station_name,
        people_count=data.people_count,
        created_at=data.created_at,
    )
