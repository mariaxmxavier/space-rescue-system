"""The ExpireRequest command contract.

What: defines the command that expires a seat request past its deadline.
When called: imported by RescueCentral.expire_request, the expire_request service and callers that build the command.
Why: a command is one frozen value, so a service receives its input already shaped and unchangeable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import Id, Instant


@dataclass(frozen=True, slots=True)
class ExpireRequest:
    """Ask central to expire a request whose deadline has passed.

    What: names the mission, the request and the current instant.
    When called: by RescueCentral.expire_request, which hands the command to the expire_request service.
    Why: a request left unanswered must close and release its seats.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    mission_id: Id
    request_id: Id
    now: Instant
