"""Business outcomes carried in a ship response envelope."""

from enum import StrEnum


class ResponseOutcome(StrEnum):
    """Name accepted, partial and refused response outcomes from the mission API."""

    ACCEPTED = "accepted"
    PARTIALLY_ACCEPTED = "partially_accepted"
    REFUSED = "refused"
