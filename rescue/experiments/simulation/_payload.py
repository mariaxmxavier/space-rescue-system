"""The response payload the runner attaches to a scheduled response event.

What: the private `_ResponsePayload` record.
Why: the runner builds one payload per response attempt and the event handler reads it back.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class _ResponsePayload:
    """One response attempt as the runner schedules it.

    What: ids, outcome, seats, attempt number and timing of a single response.
    Why: it carries everything the handler needs to record the response.
    """

    message_id: str
    mission_id: str
    request_id: str
    outcome: str
    confirmed_seats: int
    attempt_number: int
    sent_at: Decimal
    received_at: Decimal | None
    communication_rtt_seconds: Decimal | None
