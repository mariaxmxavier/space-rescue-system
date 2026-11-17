"""Normalise one ship response command.

What: normalises ids, attempt, instants, RTT and confirmed seats, checks receipt against send time and builds the CommunicationMessage.
When called: first, by record_response in rescue/application/services/communication/record_response.py.
Why: every later step reads checked values; a bad value raises DomainValidationError for the caller to turn into a rejected Result.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from rescue.application.contracts import RecordResponse
from rescue.application.shared.delivery.normalised_response import NormalisedResponse
from rescue.communication.models import CommunicationMessage
from rescue.values import (
    DomainValidationError,
    normalize_id,
    normalize_instant,
    normalize_nonnegative_quantity,
    normalize_positive_quantity,
)


def normalise_response(command: RecordResponse) -> NormalisedResponse:
    """Normalise response.

    What: normalises ids, attempt, instants, RTT and confirmed seats, rejects a receipt before the send time, and builds the ship_response CommunicationMessage.
    When called: first, by record_response in rescue/application/services/communication/record_response.py.
    Why: later steps read checked values, and a bad value raises DomainValidationError for the caller to turn into a rejected Result.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    message_id = normalize_id(command.message_id)
    request_id = normalize_id(command.request_id)
    delivery_id = normalize_id(command.delivery_id)
    attempt = normalize_positive_quantity(command.attempt_number)
    sent_at = normalize_instant(command.sent_at)
    received_at = None if command.received_at is None else normalize_instant(command.received_at)
    communication_rtt = (
        None
        if command.communication_rtt_seconds is None
        else normalize_instant(command.communication_rtt_seconds)
    )
    confirmed = normalize_nonnegative_quantity(command.confirmed_seats)
    if received_at is not None and received_at < sent_at:
        raise DomainValidationError("receipt cannot precede send time")
    message = CommunicationMessage(
        message_id=message_id,
        correlation_id=request_id,
        request_id=request_id,
        kind="ship_response",
        payload=(("outcome", command.outcome), ("confirmed_seats", confirmed)),
        sent_at=sent_at,
    )
    return NormalisedResponse(
        message,
        message_id,
        request_id,
        delivery_id,
        attempt,
        sent_at,
        received_at,
        communication_rtt,
        confirmed,
    )
