"""Play one timeline event during a simulation.

What: `play_event` routes a popped timeline event to the step that handles its kind.
When called: by the simulate loop for each event it pops.
Why: the loop should not know which step owns which event kind.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from __future__ import annotations

from rescue.experiments.simulation.events.expire_request import expire_request
from rescue.experiments.simulation.events.publish_availability import publish_availability
from rescue.experiments.simulation.events.record_response import record_response
from rescue.experiments.simulation.mobilise_mission import mobilise_mission
from rescue.experiments.simulation.session import SimulationSession
from rescue.experiments.timeline import TimelineEvent
from rescue.values import DomainValidationError


def play_event(session: SimulationSession, event: TimelineEvent) -> None:
    """Play one timeline event during a simulation.

    What: calls `mobilise_mission` for "mobilise" and the matching handler for "availability",
      "expire" and "response", passing `event.instant` as the current time.
    When called: once per popped timeline event.
    Why: each kind has exactly one step; anything else is a malformed scenario.
    Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
    """
    now = event.instant
    match event.kind:
        case "mobilise":
            mobilise_mission(session, event.payload, now)
        case "availability":
            publish_availability(session, event, now)
        case "expire":
            expire_request(session, event, now)
        case "response":
            record_response(session, event, now)
        case _:
            raise DomainValidationError(f"unknown scenario event kind: {event.kind!r}")
