"""The reason a command was rejected or ignored.

What: the closed set of machine-readable reasons carried by a Result.
When called: by services when a command cannot be applied, and by callers that report why.
Why: a closed set lets callers and tests match on a reason without parsing messages.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from enum import StrEnum


class ErrorReason(StrEnum):
    """The closed set of reasons a Result can carry.

    What: names each way a command can be refused or ignored, such as unknown_mission or late.
    When called: read by services when they build a Result, and by callers and tests that match on a reason.
    Why: a Result refuses any reason outside this set, so reasons stay checkable.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    INVALID_INPUT = "invalid_input"
    UNKNOWN_MISSION = "unknown_mission"
    UNKNOWN_SHIP = "unknown_ship"
    UNKNOWN_REQUEST = "unknown_request"
    UNKNOWN_DECISION = "unknown_decision"
    UNKNOWN_MESSAGE = "unknown_message"
    IDENTITY_CONFLICT = "identity_conflict"
    CLOSED_REQUEST = "closed_request"
    LATE = "late"
    INSUFFICIENT_DEMAND = "insufficient_demand"
    INSUFFICIENT_CAPACITY = "insufficient_capacity"
    UNAVAILABLE = "unavailable"
    EXPIRED_QUOTE = "expired_quote"
    REVISION_CONFLICT = "revision_conflict"
    DUPLICATE_SEQUENCE = "duplicate_sequence"
    STALE_SESSION = "stale_session"
    SEQUENCE_REWIND = "sequence_rewind"
    RECOVERY_OUT_OF_RANGE = "recovery_out_of_range"
    RECOVERY_LIMIT = "recovery_limit"
    RECOVERY_IN_PROGRESS = "recovery_in_progress"
    UNKNOWN_SESSION = "unknown_session"
