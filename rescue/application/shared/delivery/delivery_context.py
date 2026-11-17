"""The values the delivery steps pass to each other.

What: holds the message, ids, attempt, instants, known delivery, existing message, mission, request, envelope, session and session verdict of one delivery.
When called: built by classify_response, completed by resolve_session and read by publish_delivery, all run by record_response in rescue/application/services/communication/record_response.py.
Why: the closure that once held these values as free variables becomes an explicit value.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.communication.models import (
    CommunicationMessage,
    CommunicationSession,
    SessionEnvelope,
)
from rescue.mission.models import Mission, SeatRequest
from rescue.values import Id, Instant


@dataclass(frozen=True, slots=True)
class DeliveryContext:
    """Deliverycontext.

    What: is a frozen value that holds the message, ids, attempt, instants, confirmed seats, known delivery, existing message, mission and request, plus the envelope, session and verdict added later.
    When called: built by classify_response, completed by resolve_session and read by publish_delivery, all run by record_response in rescue/application/services/communication/record_response.py.
    Why: the values the response flow shares become one explicit value instead of free variables of a closure.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    message: CommunicationMessage
    message_id: Id
    request_id: Id
    delivery_id: Id
    attempt: int
    sent_at: Instant
    received_at: Instant | None
    communication_rtt: Instant | None
    confirmed: int
    known_delivery: tuple | None
    existing_message: tuple | None
    message_conflicts: bool
    mission: Mission | None
    request: SeatRequest | None
    envelope: SessionEnvelope | None = None
    session: CommunicationSession | None = None
    verdict: str | None = None
