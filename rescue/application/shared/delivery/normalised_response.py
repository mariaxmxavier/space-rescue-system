"""The checked fields of one ship response.

What: holds the normalised ids, attempt, instants, RTT, confirmed seats and the built message.
When called: returned by normalise_response and read by classify_response, both run by record_response in rescue/application/services/communication/record_response.py.
Why: later steps read valid values and never re-normalise the command.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.communication.models import CommunicationMessage
from rescue.values import Id, Instant


@dataclass(frozen=True, slots=True)
class NormalisedResponse:
    """Normalisedresponse.

    What: is a frozen value that holds the normalised ids, attempt, instants, RTT, confirmed seats and the built message of one ship response.
    When called: returned by normalise_response and read by classify_response, both run by record_response in rescue/application/services/communication/record_response.py.
    Why: later steps read valid values and never re-normalise the command.
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
