"""Responses a ship can send to a real request."""

from enum import StrEnum


class ReplyKind(StrEnum):
    """Distinguish confirmations, partial confirmations and refusals in a recipe."""

    CONFIRM = "confirm"
    PARTIAL = "partial"
    REFUSE = "refuse"
