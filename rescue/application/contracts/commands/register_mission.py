"""The RegisterMission command contract.

What: defines the command that registers a rescue mission.
When called: imported by RescueCentral.register_mission, the register_mission service and callers that build the command.
Why: a command is one frozen value, so a service receives its input already shaped and unchangeable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import Id, Instant


@dataclass(frozen=True, slots=True)
class RegisterMission:
    """Ask central to register a rescue mission.

    What: names the mission, its station, the people to rescue and the creation instant.
    When called: by RescueCentral.register_mission, which hands the command to the register_mission service.
    Why: a mission must exist before ships can quote or be mobilised for it.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    mission_id: Id
    station_name: str
    people_count: int
    created_at: Instant
