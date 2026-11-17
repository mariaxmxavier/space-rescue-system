"""Shared validation helpers for communication message models.

What: normalizes message kinds and payload key/value pairs.
Why: keeps message validation in one private place so every model rejects bad input alike.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import cast

from rescue.values import DomainValidationError

PayloadValue = str | int | bool | Decimal | None
Payload = tuple[tuple[PayloadValue, PayloadValue], ...]


def normalize_kind(value: object) -> str:
    """What: accepts a nonblank string as a message kind.

    Why: a blank or non-string kind cannot identify what a message carries.
    """
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError("message kind must be a nonblank string")
    return value


def normalize_payload(value: object) -> Payload:
    """What: turns an iterable of key/value pairs into an immutable payload tuple.

    Why: payloads must be hashable and free of mutable or non-primitive values.
    """
    if isinstance(value, (str, bytes)):
        raise DomainValidationError("message payload must be a collection of key/value pairs")
    try:
        entries = tuple(cast("Iterable[object]", value))
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
        if not is_primitive(key) or not is_primitive(item):
            raise DomainValidationError("payload values must be primitive immutable values")
        normalized.append((key, item))
    return tuple(normalized)


def is_primitive(value: object) -> bool:
    """What: tells whether a value is an allowed payload primitive.

    Why: only immutable primitives and finite decimals keep payloads comparable and hashable.
    """
    return (
        value is None
        or type(value) in (str, int, bool)
        or isinstance(value, Decimal)
        and value.is_finite()
    )
