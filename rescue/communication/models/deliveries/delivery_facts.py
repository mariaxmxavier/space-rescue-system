"""The primitive facts gathered about one delivery before it is classified.

What: flags about the recorded delivery, message and request, plus the request and command instants.
When called: built by the application from the store and the command, then read by the delivery rule.
Why: the rule decides from primitives alone, so it needs no mission or store types.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import DomainValidationError, Instant, normalize_instant

_FLAGS = (
    "delivery_known",
    "delivery_identical",
    "message_conflicts",
    "request_known",
    "request_open",
    "request_expired",
)


@dataclass(frozen=True, slots=True)
class DeliveryFacts:
    """Immutable facts about a delivery, its message and its request.

    What: seven flags, three optional request or receipt instants and the send instant.
    When called: constructed once per inbound delivery before the delivery rule classifies it.
    Why: an open and expired request, or an open request that is unknown, would misdirect the rule.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """

    delivery_known: bool
    delivery_identical: bool
    message_conflicts: bool
    request_known: bool
    request_open: bool
    request_expired: bool
    submitted_at: Instant | None
    deadline: Instant | None
    sent_at: Instant
    received_at: Instant | None

    def __post_init__(self) -> None:
        for name in _FLAGS:
            if type(getattr(self, name)) is not bool:
                raise DomainValidationError(f"{name} must be a bool")
        if self.request_open and self.request_expired:
            raise DomainValidationError("a request cannot be both open and expired")
        if not self.request_known and (self.request_open or self.request_expired):
            raise DomainValidationError("an unknown request cannot be open or expired")
        for name in ("submitted_at", "deadline", "received_at"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, normalize_instant(value))
        object.__setattr__(self, "sent_at", normalize_instant(self.sent_at))
