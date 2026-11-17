"""Primitive values shared by the domain's inner layers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterable, TypeVar

Id = str
Instant = Decimal

T = TypeVar("T")


class DomainValidationError(ValueError):
    """Raised when an input cannot represent a valid domain value."""


def normalize_id(value: object) -> Id:
    """Validate an identifier without changing its case or surrounding spaces."""
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError("identifier must be a nonblank string")
    return value


def normalize_quantity(value: object) -> int:
    """Validate a positive, exact integer quantity (booleans are not integers here)."""
    return normalize_positive_quantity(value)


def normalize_nonnegative_quantity(value: object) -> int:
    if type(value) is not int or value < 0:
        raise DomainValidationError("quantity must be a nonnegative integer")
    return value


def normalize_positive_quantity(value: object) -> int:
    if type(value) is not int or value <= 0:
        raise DomainValidationError("quantity must be a positive integer")
    return value


def normalize_instant(value: object) -> Instant:
    """Normalize integer or decimal-string seconds to finite nonnegative Decimal."""
    if isinstance(value, bool) or isinstance(value, float):
        raise DomainValidationError("instant must be an integer or decimal string")
    if not isinstance(value, (int, str, Decimal)):
        raise DomainValidationError("instant must be an integer, decimal string, or Decimal")
    try:
        instant = Decimal(value)
    except InvalidOperation, ValueError:
        raise DomainValidationError("instant must be a valid decimal value") from None
    if not instant.is_finite() or instant < 0:
        raise DomainValidationError("instant must be finite and nonnegative")
    return instant


def immutable_tuple(values: Iterable[T]) -> tuple[T, ...]:
    """Copy an iterable into an immutable collection boundary."""
    if isinstance(values, (str, bytes)):
        raise DomainValidationError("a string is not a collection of snapshot values")
    return tuple(values)


@dataclass(frozen=True, slots=True)
class TransitionContext:
    event_id: Id
    at: Instant
    reason: str
    message_id: Id | None = None

    def __post_init__(self) -> None:
        normalize_id(self.event_id)
        object.__setattr__(self, "at", normalize_instant(self.at))
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise DomainValidationError("transition reason must be nonblank")
        if self.message_id is not None:
            normalize_id(self.message_id)
