"""Mobilise one mission during a simulation.

What: `mobilise_mission` asks the central for ships and creates a request for each selected one.
When called: by the runner when a mobilise event fires.
Why: a mobilise event must turn into requests and their follow-up events on the timeline.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from __future__ import annotations

from decimal import Decimal

from rescue.application.contracts import CreateRequest, Mobilise
from rescue.experiments.simulation.schedule_request_events import schedule_request_events
from rescue.experiments.simulation.session import SimulationSession
from rescue.mission.rules import progress
from rescue.values import DomainValidationError


def mobilise_mission(session: SimulationSession, mission_id: str, now: Decimal) -> None:
    """Mobilise one mission during a simulation.

    What: returns when no more seats are needed; otherwise selects ships through the central,
      raises `DomainValidationError` when the selection is not applied, creates one request per
      selected evaluation and schedules the events of each applied request.
    When called: once per mobilise event.
    Why: the central owns selection and creation, so the runner only feeds the results onward.
    Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
    """
    handle = session.handle
    mission = next(
        item for item in handle.store.snapshot().missions if item.mission_id == mission_id
    )
    if progress(mission).additional_needed == 0:
        return
    selection = handle.central.mobilise(
        Mobilise(
            mission_id=mission_id,
            policy_id=session.policy.policy_id,
            policy_revision=session.policy.revision,
            now=now,
        )
    )
    if selection.status != "applied":
        raise DomainValidationError(f"scenario mobilisation failed: {selection.reason}")
    for evaluation in selection.value.selected:
        created = handle.central.create_request(
            CreateRequest(
                command_id=handle.id_source.next_id("command"),
                mission_id=mission_id,
                ship_id=evaluation.ship_id,
                requested_seats=evaluation.proposed_seats,
                revision_id=evaluation.revision.revision_id,
                decision_id=selection.value.decision_id,
                now=now,
            )
        )
        if created.status == "applied":
            schedule_request_events(session, mission_id, created.value)
