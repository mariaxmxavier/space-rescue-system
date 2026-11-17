"""Record a ship response.

What: records the event's response and reschedules mobilise after a first received response.
When called: when the timeline pops a "response" event.
Why: a first applied response changes demand, so the mission is mobilised again.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from __future__ import annotations

from decimal import Decimal

from rescue.application.contracts import RecordResponse
from rescue.experiments.simulation._payload import _ResponsePayload
from rescue.experiments.simulation.session import SimulationSession
from rescue.experiments.timeline import TimelineEvent


def record_response(session: SimulationSession, event: TimelineEvent, now: Decimal) -> None:
    """Record a ship response.

    What: calls the central's `record_response` and schedules a "mobilise" event at `now`
      when attempt 1 was received and applied.
    When called: for each "response" timeline event.
    Why: duplicate, lost or unapplied attempts change nothing, so they schedule nothing.
    Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
    """
    payload: _ResponsePayload = event.payload
    response = session.handle.central.record_response(
        RecordResponse(
            message_id=payload.message_id,
            delivery_id=session.handle.id_source.next_id("delivery"),
            attempt_number=payload.attempt_number,
            request_id=payload.request_id,
            outcome=payload.outcome,
            confirmed_seats=payload.confirmed_seats,
            sent_at=payload.sent_at,
            received_at=payload.received_at,
            communication_rtt_seconds=payload.communication_rtt_seconds,
        )
    )
    if (
        payload.received_at is not None
        and payload.attempt_number == 1
        and response.status == "applied"
    ):
        session.timeline.schedule(
            TimelineEvent(
                instant=now,
                kind="mobilise",
                scenario_sequence=next(session.sequence),
                payload=payload.mission_id,
            )
        )
