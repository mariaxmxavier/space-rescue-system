"""Schedule the response events for one seat request.

What: `schedule_response` queues one response event, or two when the profile duplicates it.
When called: by `schedule_request_events` when a scripted rule matches a request.
Why: the ship's profile decides the delay, loss, duplication and priority of the response.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from rescue.experiments.models import CommunicationProfile, ScriptedResponse
from rescue.experiments.simulation._payload import _ResponsePayload
from rescue.experiments.simulation.scripted_outcome import scripted_outcome
from rescue.experiments.simulation.session import SimulationSession
from rescue.experiments.timeline import TimelineEvent
from rescue.mission.models import Mission


def _response_event(
    expected_receipt: Decimal,
    priority: int,
    sequence: int,
    payload: _ResponsePayload,
) -> TimelineEvent:
    """What: wraps a response payload in a timeline event.

    Why: the first attempt and the duplicate share one event shape.
    """
    return TimelineEvent(
        instant=expected_receipt,
        kind="response",
        scenario_sequence=sequence,
        payload=payload,
        priority=priority,
    )


def schedule_response(
    session: SimulationSession,
    rule: ScriptedResponse,
    mission: Mission,
    request,
    ordinal: int,
    profile: CommunicationProfile | None,
    message_id: str,
) -> None:
    """Schedule the response events for one seat request.

    What: resolves the scripted outcome, applies the profile's delays, loss, duplication and
      reordering, and schedules attempt 1 and, when duplicated, attempt 2.
    When called: once per request that a scripted rule matches.
    Why: communication faults live in the profile, so the timeline carries them as plain events.
    Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
    """
    outbound = Decimal("0") if profile is None else profile.outbound_delay_seconds
    decision = Decimal("0") if profile is None else profile.decision_delay_seconds
    returning = Decimal("0") if profile is None else profile.return_delay_seconds
    outcome, confirmed = scripted_outcome(rule, request.requested_seats, session.rng)
    sent_at = request.submitted_at + outbound + decision
    expected_receipt = sent_at + returning
    lost = profile is not None and ordinal in profile.loss_rule
    duplicated = profile is not None and ordinal in profile.duplication_rule and not lost
    delivery_priority = 2 if profile is not None and ordinal in profile.reordering_rule else 1

    first = _ResponsePayload(
        message_id=message_id,
        mission_id=mission.mission_id,
        request_id=request.request_id,
        outcome=outcome.value,
        confirmed_seats=confirmed,
        attempt_number=1,
        sent_at=sent_at,
        received_at=None if lost else expected_receipt,
        communication_rtt_seconds=None if lost else outbound + returning,
    )
    session.timeline.schedule(
        _response_event(expected_receipt, delivery_priority, next(session.sequence), first)
    )
    if duplicated:
        session.timeline.schedule(
            _response_event(
                expected_receipt,
                delivery_priority,
                next(session.sequence),
                replace(first, attempt_number=2),
            )
        )
