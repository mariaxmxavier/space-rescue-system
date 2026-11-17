"""Private validators shared by the mission models.

What: turn raw boundary inputs into names, identifiers, instants and signed quantities.
Why: one definition of each check keeps all mission models rejecting the same input the same way.
"""

from __future__ import annotations

from rescue import values


def normalize_name(value: object, label: str) -> str:
    """Return a nonblank string unchanged or raise a labelled domain error.

    What: accepts a str with at least one non-space character and returns it as given.
    Why: a blank name is reported with its field label so the caller sees which field failed.
    """
    if not isinstance(value, str) or not value.strip():
        raise values.DomainValidationError(f"{label} must be a nonblank string")
    return value


def optional_id(value: object, label: str) -> values.Id | None:
    """Return a normalised identifier, or None when no identifier was given.

    What: passes None through and otherwise validates the value as an identifier.
    Why: optional references like quote or message ids reject blank text but may be absent.
    """
    if value is None:
        return None
    try:
        return values.normalize_id(value)
    except ValueError as error:
        raise values.DomainValidationError(f"{label} must be a nonblank identifier") from error


def optional_instant(value: object) -> values.Instant | None:
    """Return a normalised instant, or None when no instant was given.

    What: passes None through and otherwise normalises the value with the instant wrapper.
    Why: optional timestamps such as a response receipt are absent until the event happens.
    """
    if value is None:
        return None
    return values.normalize_instant(value)


def signed_quantity(value: object, label: str) -> int:
    """Return an integer that may be negative, rejecting booleans and other types.

    What: accepts only exact int instances, including zero and negative values.
    Why: deltas may be negative, while bool is an int subclass that must not pass as a quantity.
    """
    if type(value) is not int:
        raise values.DomainValidationError(f"{label} must be an integer")
    return value
