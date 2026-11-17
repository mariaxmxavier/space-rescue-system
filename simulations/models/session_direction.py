"""Directions carried by sequenced mission response envelopes."""

from enum import StrEnum


class SessionDirection(StrEnum):
    """Identify whether a session envelope travels to or from central."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"
