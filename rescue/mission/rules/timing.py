"""Waiting and response-time projection for one seat request.

What: reads a SeatRequest at an observation time and returns its RequestTiming without changing it.
When called: by callers that show how long a ship has been asked or how long it took to answer.
Why: waiting and response times are derived from the stored timestamps, so they never disagree
  with the request they describe.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from __future__ import annotations

from rescue.mission.models.mission.seat_request import SeatRequest
from rescue.mission.models.projections.request_timing import RequestTiming
from rescue.values import DomainValidationError, normalize_instant


def timing(request: SeatRequest, now: object) -> RequestTiming:
    """Project waiting and response time for one request without mutating it.

    What: returns the time still waited for a request with no receipt, or the submission-to-receipt
      time with zero wait for an answered request.
    When called: by read-only callers at an observation time, for pending and answered requests.
    Why: a request observed before its submission, or a value that is not a SeatRequest, has no
      meaningful timing, so both are rejected rather than projected.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """
    if not isinstance(request, SeatRequest):
        raise DomainValidationError("timing requires a SeatRequest")
    instant = normalize_instant(now)
    if instant < request.submitted_at:
        raise DomainValidationError("observation time cannot precede request submission")
    if request.response_received_at is None:
        return RequestTiming(
            submitted_at=request.submitted_at,
            response_received_at=None,
            waiting_seconds=instant - request.submitted_at,
            response_elapsed_seconds=None,
        )
    return RequestTiming(
        submitted_at=request.submitted_at,
        response_received_at=request.response_received_at,
        waiting_seconds=0,
        response_elapsed_seconds=request.response_received_at - request.submitted_at,
    )
