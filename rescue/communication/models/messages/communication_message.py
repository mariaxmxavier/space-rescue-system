"""Immutable logical message a ship sends in response to a request.

What: the message identity, correlation, kind, primitive payload and send time.
When called: built by the communication flow when a ship sends a message, and read when deliveries are matched.
Why: validation at construction keeps identity and content fixed across retries.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.communication.models._validation import Payload, normalize_kind, normalize_payload
from rescue.values import Id, Instant, normalize_id, normalize_instant


@dataclass(frozen=True, slots=True)
class CommunicationMessage:
    """Immutable logical message that retries reuse under fresh envelopes.

    What: one message with non-blank ids, a kind, primitive payload pairs and a normalised send time.
    When called: constructed when a ship sends a reply; compared when deliveries are correlated.
    Why: rejecting bad ids, kinds and payloads at construction keeps retries and duplicates comparable.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """

    message_id: Id
    correlation_id: Id
    kind: str
    payload: Payload
    sent_at: Instant
    request_id: Id

    def __post_init__(self) -> None:
        normalize_id(self.message_id)
        normalize_id(self.correlation_id)
        normalize_id(self.request_id)
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(self, "payload", normalize_payload(self.payload))
        object.__setattr__(self, "sent_at", normalize_instant(self.sent_at))
