"""One delivery attempt of a message and how it was received.

What: the immutable record of an attempt, its receipt time, disposition, reason, observed RTT
  and session envelope.
When called: built by the delivery classification and read by the application when it records deliveries.
Why: the receipt, loss, RTT and envelope rules hold at construction, so no stored delivery
  contradicts itself.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rescue.communication.models.sessions.session_envelope import SessionEnvelope
from rescue.communication.models.vocabulary.delivery_disposition import DeliveryDisposition
from rescue.communication.models.vocabulary.delivery_reason import DeliveryReason
from rescue.communication.models.vocabulary.flow_direction import FlowDirection
from rescue.values import (
    DomainValidationError,
    Id,
    Instant,
    normalize_id,
    normalize_instant,
    normalize_positive_quantity,
)


def _vocabulary[T: (DeliveryDisposition, DeliveryReason)](
    kind: type[T], label: str, value: object
) -> T:
    """What: converts a disposition or reason given as a member or a string into its closed vocabulary member.
    Why: rejects blank and unknown values, so a delivery can only carry a named outcome from the closed vocabulary.
    """
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"delivery {label} must be a nonblank string")
    try:
        return kind(value)
    except ValueError:
        raise DomainValidationError(f"delivery {label} must be a known {label}") from None


@dataclass(frozen=True, slots=True)
class MessageDelivery:
    """One attempt to deliver a message, with its disposition and reason.

    What: the delivery id, attempt number, optional receipt time, disposition, reason, optional RTT
      and optional session envelope.
    When called: created for each attempt once central knows whether and when the message arrived.
    Why: a lost attempt has no receipt time, RTT or envelope, every other attempt has a receipt
      time, and an envelope, when present, is inbound.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """

    delivery_id: Id
    attempt_number: int
    received_at: Instant | None = None
    disposition: DeliveryDisposition = field(kw_only=True)
    reason: DeliveryReason = field(kw_only=True)
    communication_rtt_seconds: Instant | None = field(default=None, kw_only=True)
    envelope: SessionEnvelope | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        normalize_id(self.delivery_id)
        object.__setattr__(
            self,
            "attempt_number",
            normalize_positive_quantity(self.attempt_number),
        )
        object.__setattr__(
            self, "disposition", _vocabulary(DeliveryDisposition, "disposition", self.disposition)
        )
        object.__setattr__(self, "reason", _vocabulary(DeliveryReason, "reason", self.reason))
        if self.received_at is not None:
            object.__setattr__(self, "received_at", normalize_instant(self.received_at))
        is_lost = self.disposition is DeliveryDisposition.LOST
        if is_lost != (self.received_at is None):
            raise DomainValidationError("lost deliveries must have no receipt time")
        if self.communication_rtt_seconds is not None:
            object.__setattr__(
                self,
                "communication_rtt_seconds",
                normalize_instant(self.communication_rtt_seconds),
            )
        if is_lost and self.communication_rtt_seconds is not None:
            raise DomainValidationError("lost deliveries cannot report an observed RTT")
        if self.envelope is not None:
            if is_lost:
                raise DomainValidationError("lost deliveries cannot carry a session envelope")
            if not isinstance(self.envelope, SessionEnvelope):
                raise DomainValidationError("delivery envelope must be a session envelope")
            if self.envelope.direction is not FlowDirection.INBOUND:
                raise DomainValidationError("delivery envelope must be inbound")
