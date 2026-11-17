"""Request closure operations available to timeline recipes."""

from enum import StrEnum


class CloseKind(StrEnum):
    """Identify an explicit cancellation or expiration transition."""

    CANCEL = "cancel"
    EXPIRE = "expire"
