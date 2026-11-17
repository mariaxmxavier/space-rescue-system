"""Closed vocabulary of reasons a communication recovery request is rejected.

What: the five reasons a recovery request or inbound synchronisation control can be refused.
When called: returned by the communication rules that check a recovery request or a sequence
  control, and compared by the application layer that maps it to an error reason.
Why: a fixed name set makes each refusal explicit and comparable across sessions and reports.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from enum import StrEnum


class RecoveryRejection(StrEnum):
    """Reason a communication recovery request or sequence control was rejected.

    What: STALE_SESSION for an inactive session version, RECOVERY_OUT_OF_RANGE for a range
      that is not retained, RECOVERY_LIMIT for a count outside 1 to 1000,
      RECOVERY_IN_PROGRESS for a second overlapping request, and SEQUENCE_REWIND for a
      synchronisation that would move the inbound expectation backwards.
    When called: returned before any state changes, so the caller can report the refusal
      without a business effect.
    Why: a named refusal leaves session counters and recoverable reports unchanged and says
      why the request had no effect (Constitution III).
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """

    STALE_SESSION = "stale_session"
    RECOVERY_OUT_OF_RANGE = "recovery_out_of_range"
    RECOVERY_LIMIT = "recovery_limit"
    RECOVERY_IN_PROGRESS = "recovery_in_progress"
    SEQUENCE_REWIND = "sequence_rewind"
