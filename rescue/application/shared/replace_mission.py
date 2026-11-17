"""Replace a registered mission in a run state.

What: returns the state with the mission swapped by id, and refuses an unregistered mission.
When called: by every service that changes a mission.
Why: the update path never adds a mission, so registration stays a separate command.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.mission.models import Mission
from rescue.state import RunState
from rescue.values import DomainValidationError


def replace_mission(state: RunState, mission: Mission) -> RunState:
    """Replace mission.

    What: returns the state with the mission replaced by the updated one, and raises DomainValidationError when the mission is not registered.
    When called: by open_request, close_pending_request and record_response.
    Why: a mission update must not create a mission that was never registered.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    if not any(item.mission_id == mission.mission_id for item in state.missions):
        raise DomainValidationError("cannot update an unregistered mission")
    return replace(
        state,
        missions=tuple(
            mission if item.mission_id == mission.mission_id else item for item in state.missions
        ),
    )
