"""Immutable logical messages and their individual delivery attempts."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from rescue.values import (
    DomainValidationError,
    Id,
    Instant,
    normalize_id,
    normalize_instant,
    normalize_positive_quantity,
)

PayloadValue = str | int | bool | Decimal | None
Payload = tuple[tuple[PayloadValue, PayloadValue], ...]


def _normalize_kind(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError("message kind must be a nonblank string")
    return value


def _normalize_payload(value: object) -> Payload:
    if isinstance(value, (str, bytes)):
        raise DomainValidationError("message payload must be a collection of key/value pairs")
    try:
        entries = tuple(value)  # type: ignore[arg-type]
    except TypeError:
        raise DomainValidationError("message payload must be iterable") from None

    normalized: list[tuple[PayloadValue, PayloadValue]] = []
    for entry in entries:
        if isinstance(entry, (str, bytes)):
            raise DomainValidationError("each payload entry must be a key/value pair")
        try:
            pair = tuple(entry)
        except TypeError:
            raise DomainValidationError("each payload entry must be a key/value pair") from None
        if len(pair) != 2:
            raise DomainValidationError("each payload entry must contain exactly two values")
        key, item = pair
        if not _is_primitive(key) or not _is_primitive(item):
            raise DomainValidationError("payload values must be primitive immutable values")
        normalized.append((key, item))
    return tuple(normalized)


def _is_primitive(value: object) -> bool:
    return (
        value is None
        or type(value) in (str, int, bool)
        or isinstance(value, Decimal)
        and value.is_finite()
    )


@dataclass(frozen=True, slots=True)
class CommunicationMessage:
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
        object.__setattr__(self, "kind", _normalize_kind(self.kind))
        object.__setattr__(self, "payload", _normalize_payload(self.payload))
        object.__setattr__(self, "sent_at", normalize_instant(self.sent_at))


@dataclass(frozen=True, slots=True)
class MessageDelivery:
    delivery_id: Id
    attempt_number: int
    received_at: Instant | None = None
    disposition: str = field(kw_only=True)
    reason: str = field(kw_only=True)
    communication_rtt_seconds: Instant | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        normalize_id(self.delivery_id)
        object.__setattr__(
            self,
            "attempt_number",
            normalize_positive_quantity(self.attempt_number),
        )
        if not isinstance(self.disposition, str) or not self.disposition.strip():
            raise DomainValidationError("delivery disposition must be a nonblank string")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise DomainValidationError("delivery reason must be a nonblank string")
        if self.received_at is not None:
            object.__setattr__(self, "received_at", normalize_instant(self.received_at))
        if (self.disposition == "lost") != (self.received_at is None):
            raise DomainValidationError("lost deliveries must have no receipt time")
        if self.communication_rtt_seconds is not None:
            object.__setattr__(
                self,
                "communication_rtt_seconds",
                normalize_instant(self.communication_rtt_seconds),
            )
        if self.disposition == "lost" and self.communication_rtt_seconds is not None:
            raise DomainValidationError("lost deliveries cannot report an observed RTT")
