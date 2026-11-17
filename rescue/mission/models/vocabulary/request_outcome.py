"""Closed vocabulary of seat request outcomes.

What: the six values a seat request outcome can take. PENDING is the only
  value that leaves the request open.
When called: stored on SeatRequest.outcome and compared by the mission rules
  that record a ship's answer.
Why: an enum makes an unknown outcome fail on conversion, not later in a string
  comparison (Constitution II).
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from __future__ import annotations

from enum import StrEnum


class RequestOutcome(StrEnum):
    """Outcome of one ship's answer to a seat request.

    What: PENDING while the ship has not answered. ACCEPTED, PARTIALLY_ACCEPTED,
      REFUSED, CANCELLED and EXPIRED close the request.
    When called: assigned to SeatRequest.outcome when the request is created and
      replaced when a final answer is applied.
    Why: a closed request must name its final state, so no request can stop at an
      unnamed value.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """

    PENDING = "pending"
    ACCEPTED = "accepted"
    PARTIALLY_ACCEPTED = "partially_accepted"
    REFUSED = "refused"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

    @classmethod
    def final(cls) -> tuple[RequestOutcome, ...]:
        """The five closed outcomes, in declaration order.

        What: every member except PENDING, as a tuple.
        When called: by the mission rule that applies a ship's answer, to reject any
          outcome that would not close the request.
        Why: PENDING is never a valid answer, so a closed request always holds a final state.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
        """
        return tuple(member for member in cls if member is not cls.PENDING)
