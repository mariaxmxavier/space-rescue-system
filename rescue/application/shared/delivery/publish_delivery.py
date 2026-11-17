"""Append one delivery to the indices and, when received, its decision report.

What: builds the MessageDelivery with its envelope, records it, and for a received delivery issues the report on the accepted session and publishes that session.
When called: by record_response in rescue/application/services/communication/record_response.py, once per recorded outcome.
Why: every recorded outcome shares one write path, so the indices, the session and its retained reports stay aligned in one returned state.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.application.shared.delivery.delivery_context import DeliveryContext
from rescue.application.shared.replace_session import replace_session
from rescue.communication import rules as communication_rules
from rescue.communication.models import MessageDelivery
from rescue.mission.models import Mission
from rescue.state import RunState


def publish_delivery(
    target_state: RunState,
    context: DeliveryContext,
    disposition: str,
    delivery_reason: str,
    *,
    keep_message: bool = True,
    decided_mission: Mission | None = None,
    report: bool = True,
) -> RunState:
    """Publish delivery.

    What: builds the MessageDelivery, adds it and the message to the indices, and for a received delivery issues the report on the session and stores that session.
    When called: by record_response in rescue/application/services/communication/record_response.py, once per recorded outcome.
    Why: every recorded outcome shares one write path, so the indices, the session and its retained reports stay aligned in one returned state.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    delivery_id = context.delivery_id
    message_id = context.message_id
    message = context.message
    existing_message = context.existing_message
    mission = context.mission
    session = context.session
    delivery = MessageDelivery(
        delivery_id=delivery_id,
        attempt_number=context.attempt,
        received_at=context.received_at,
        disposition=disposition,
        reason=delivery_reason,
        communication_rtt_seconds=(
            None if context.received_at is None else context.communication_rtt
        ),
        envelope=context.envelope,
    )
    messages = target_state.message_index
    if keep_message:
        if existing_message is None:
            messages = (*messages, (message, (delivery,)))
        else:
            messages = tuple(
                (item[0], (*item[1], delivery)) if item is existing_message else item
                for item in messages
            )
    recorded = replace(
        target_state,
        message_index=messages,
        delivery_index=(
            *target_state.delivery_index,
            (delivery_id, message_id, delivery),
        ),
    )
    if session is None or not report:
        return recorded
    history = () if mission is None else mission.history
    decided = history if decided_mission is None else decided_mission.history
    issued, _report = communication_rules.issue_report(
        session,
        report_id=f"report-{delivery_id}",
        message_id=message_id,
        delivery_id=delivery_id,
        mission_id=None if mission is None else mission.mission_id,
        disposition=disposition,
        reason=delivery_reason,
        mission_sequence=(decided[-1].mission_sequence if len(decided) > len(history) else None),
        after_mission_sequence=history[-1].mission_sequence if history else 0,
    )
    return replace_session(recorded, issued)
