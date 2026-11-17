"""Gather the delivery facts and classify one ship response.

What: looks up the known delivery, existing message, mission and request, then asks classify_delivery for the decision; returns the context with the decision.
When called: second, by record_response in rescue/application/services/communication/record_response.py.
Why: the decision and the facts it was made from travel together to the later steps.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from rescue.application.shared.delivery.delivery_context import DeliveryContext
from rescue.application.shared.delivery.normalised_response import NormalisedResponse
from rescue.communication.models import DeliveryFacts
from rescue.communication.rules import classify_delivery
from rescue.mission.models import RequestOutcome
from rescue.state import RunState


def classify_response(state: RunState, normalised: NormalisedResponse):
    """Classify response.

    What: looks up the known delivery, the existing message, the mission and the request, asks classify_delivery for the decision, and returns the DeliveryContext with the decision.
    When called: second, by record_response in rescue/application/services/communication/record_response.py.
    Why: the decision and the facts it was made from travel together to the later steps.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    message = normalised.message
    message_id = normalised.message_id
    request_id = normalised.request_id
    delivery_id = normalised.delivery_id
    attempt = normalised.attempt
    sent_at = normalised.sent_at
    received_at = normalised.received_at
    communication_rtt = normalised.communication_rtt
    known_delivery = next(
        (
            item
            for item in state.delivery_index
            if isinstance(item, tuple) and len(item) == 3 and item[0] == delivery_id
        ),
        None,
    )
    existing_message = next(
        (
            item
            for item in state.message_index
            if isinstance(item, tuple) and len(item) == 2 and item[0].message_id == message_id
        ),
        None,
    )
    existing_delivery = None if known_delivery is None else known_delivery[2]
    same_message = existing_message is not None and existing_message[0] == message
    mission = next(
        (
            candidate
            for candidate in state.missions
            if any(item.request_id == request_id for item in candidate.requests)
        ),
        None,
    )
    request = (
        None
        if mission is None
        else next(item for item in mission.requests if item.request_id == request_id)
    )
    message_conflicts = existing_message is not None and not same_message
    decision = classify_delivery(
        DeliveryFacts(
            delivery_known=known_delivery is not None,
            delivery_identical=(
                known_delivery is not None
                and known_delivery[1] == message_id
                and same_message
                and existing_delivery.attempt_number == attempt
                and existing_delivery.received_at == received_at
                and existing_delivery.communication_rtt_seconds == communication_rtt
            ),
            message_conflicts=message_conflicts,
            request_known=request is not None,
            request_open=request is not None and request.outcome == RequestOutcome.PENDING,
            request_expired=request is not None and request.outcome == RequestOutcome.EXPIRED,
            submitted_at=None if request is None else request.submitted_at,
            deadline=None if request is None else request.response_deadline,
            sent_at=sent_at,
            received_at=received_at,
        )
    )
    context = DeliveryContext(
        message=message,
        message_id=message_id,
        request_id=request_id,
        delivery_id=delivery_id,
        attempt=attempt,
        sent_at=sent_at,
        received_at=received_at,
        communication_rtt=communication_rtt,
        confirmed=normalised.confirmed,
        known_delivery=known_delivery,
        existing_message=existing_message,
        message_conflicts=message_conflicts,
        mission=mission,
        request=request,
    )
    return context, decision
