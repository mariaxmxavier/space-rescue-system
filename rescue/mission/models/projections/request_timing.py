"""Read-only elapsed-time view of one seat request.

What: the submission time, the receipt time if any, the time still waited and the response time.
When called: built by the timing rule for a SeatRequest at an observation time, and read by
  callers that show how long a ship has been asked or how long it took to answer.
Why: waiting and response times are derived from the stored timestamps, so they never contradict them.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.mission.models._validation import optional_instant
from rescue.values import DomainValidationError, Instant, normalize_instant


@dataclass(frozen=True, slots=True)
class RequestTiming:
    """Elapsed-time projection for one immutable request snapshot.

    What: waiting_seconds is the time still waited on a request with no receipt, and is zero once
      a receipt exists; response_elapsed_seconds is the time from submission to receipt, or None.
    When called: returned by the timing rule and never stored on SeatRequest.
    Why: a receipt before submission, or an elapsed figure that disagrees with the timestamps,
      would report a ship's answer time wrongly.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """

    submitted_at: Instant
    response_received_at: Instant | None
    waiting_seconds: Instant
    response_elapsed_seconds: Instant | None

    def __post_init__(self) -> None:
        submitted_at = normalize_instant(self.submitted_at)
        received_at = optional_instant(self.response_received_at)
        waiting = normalize_instant(self.waiting_seconds)
        elapsed = optional_instant(self.response_elapsed_seconds)
        if received_at is None:
            if elapsed is not None:
                raise DomainValidationError("response elapsed time requires a receipt time")
        else:
            if received_at < submitted_at:
                raise DomainValidationError("response receipt cannot precede submission")
            if elapsed != received_at - submitted_at or waiting != 0:
                raise DomainValidationError("response timing projection is inconsistent")
        object.__setattr__(self, "submitted_at", submitted_at)
        object.__setattr__(self, "response_received_at", received_at)
        object.__setattr__(self, "waiting_seconds", waiting)
        object.__setattr__(self, "response_elapsed_seconds", elapsed)
