"""Find a registered mission in a run state.

What: returns the mission with this id, or None when the run has none.
When called: by most services before they read or change a mission.
Why: one lookup normalises the id the same way for every service.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from rescue.mission.models import Mission
from rescue.state import RunState
from rescue.values import normalize_id


def find_mission(state: RunState, mission_id: str) -> Mission | None:
    """Find mission.

    What: returns the mission with the normalised id from the state, or None.
    When called: by mobilise, open_request, close_pending_request, register_mission, publish_offer, request_quotes, get_history and get_progress.
    Why: one lookup definition for every service that reads a mission.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    normalized = normalize_id(mission_id)
    return next((item for item in state.missions if item.mission_id == normalized), None)
