"""Turn a supplied status into its named value, or refuse it.

When: called by every market entity that has a status, during construction.
Why: statuses are a closed vocabulary; a typo must fail at once, not travel as a free string.
Diagram: ShipMarket class-diagram.mmd (namespaces/ShipMarket).
"""

from __future__ import annotations

from enum import StrEnum

from rescue.values import DomainValidationError


def parse_named[E: StrEnum](vocabulary: type[E], value: object, field_name: str) -> E:
    """Return the member of `vocabulary` equal to `value`.

    When: an entity's `__post_init__` normalises its status field.
    Why: one place gives every status the same check and the same error message.
    Diagram: ShipMarket class-diagram.mmd (namespaces/ShipMarket).
    """
    try:
        return vocabulary(value)
    except ValueError:
        allowed = sorted(member.value for member in vocabulary)
        raise DomainValidationError(f"{field_name} must be one of {allowed}") from None
