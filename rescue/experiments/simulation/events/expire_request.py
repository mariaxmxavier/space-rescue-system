"""Expire a request whose deadline passed.

What: expires the event's request and reschedules mobilise for its mission at the same instant.
When called: when the timeline pops an "expire" event.
Why: an expired request frees demand, so the mission must be mobilised again.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from __future__ import annotations

from decimal import Decimal

from rescue.application.contracts import ExpireRequest
from rescue.experiments.simulation.session import SimulationSession
from rescue.experiments.timeline import TimelineEvent


def expire_request(session: SimulationSession, event: TimelineEvent, now: Decimal) -> None:
    """Expire a request whose deadline passed.

    What: calls the central's `expire_request` and schedules a "mobilise" event at `now`.
    When called: for each "expire" timeline event.
    Why: only an applied expiry changes demand, so only then is mobilise rescheduled.
    Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
    """
    mission_id, request_id = event.payload
    expired = session.handle.central.expire_request(
        ExpireRequest(
            mission_id=mission_id,
            request_id=request_id,
            now=now,
        )
    )
    if expired.status == "applied":
        session.timeline.schedule(
            TimelineEvent(
                instant=now,
                kind="mobilise",
                scenario_sequence=next(session.sequence),
                payload=mission_id,
            )
        )
