"""The RecordResponse command contract.

What: defines the command that records a ship response delivery.
When called: imported by RescueCentral.record_response, the record_response service and callers that build the command.
Why: a command is one frozen value, so a service receives its input already shaped and unchangeable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rescue.values import Id, Instant

if TYPE_CHECKING:
    from rescue.communication.models import SessionEnvelope


@dataclass(frozen=True, slots=True)
class RecordResponse:
    """Ask central to record a ship response to a request.

    What: carries the message and delivery ids, the outcome, confirmed seats, timing and optional session envelope.
    When called: by RescueCentral.record_response, which hands the command to the record_response service.
    Why: the ship answer decides whether the request is confirmed, partly confirmed or declined.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    message_id: Id
    delivery_id: Id
    attempt_number: int
    request_id: Id
    outcome: str
    confirmed_seats: int
    sent_at: Instant
    received_at: Instant | None
    communication_rtt_seconds: Instant | None = None
    envelope: SessionEnvelope | None = None
