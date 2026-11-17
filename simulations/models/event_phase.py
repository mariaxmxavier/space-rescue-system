"""Stable virtual-timeline phase ordering."""

from enum import IntEnum


class EventPhase(IntEnum):
    """Order events at the same logical time before their ordinal tie-breaker."""

    FLEET_CHANGE = 0
    CLOSURE = 1
    DELIVERY = 2
    SOLVER_ROUND = 3
