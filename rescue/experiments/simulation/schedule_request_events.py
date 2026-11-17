"""Schedule the events that follow a newly created request.

What: `schedule_request_events` queues the request's expiry and, when a rule matches, its response.
When called: by `mobilise_mission` for each request the central applied.
Why: the timeline must hold the deadline and the scripted answer before the run reaches them.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from __future__ import annotations

from rescue.experiments.simulation.schedule_response import schedule_response
from rescue.experiments.simulation.session import SimulationSession
from rescue.experiments.timeline import TimelineEvent


def schedule_request_events(session: SimulationSession, mission_id: str, request) -> None:
    """Schedule the events that follow a newly created request.

    What: schedules an expire event when the request has a deadline, advances the ship's request
      ordinal, and schedules a response when a rule matches that ship and ordinal.
    When called: once per applied request during mobilisation.
    Why: the ordinal selects the scripted rule, and the message id is drawn only when one matches.
    Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
    """
    if request.response_deadline is not None:
        session.timeline.schedule(
            TimelineEvent(
                instant=request.response_deadline,
                kind="expire",
                scenario_sequence=next(session.sequence),
                payload=(mission_id, request.request_id),
            )
        )
    ordinals = session.ship_ordinals
    ordinals[request.ship_id] = ordinals.get(request.ship_id, 0) + 1
    rule = session.response_rules.get((request.ship_id, ordinals[request.ship_id]))
    if rule is not None:
        missions = session.handle.store.snapshot().missions
        mission = next(item for item in missions if item.mission_id == mission_id)
        schedule_response(
            session,
            rule,
            mission,
            request,
            ordinals[request.ship_id],
            session.profiles.get(request.ship_id),
            session.handle.id_source.next_id("message"),
        )
