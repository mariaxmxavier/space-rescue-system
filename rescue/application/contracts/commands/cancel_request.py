"""The CancelRequest command contract.

What: defines the command that cancels a pending seat request.
When called: imported by RescueCentral.cancel_request, the cancel_request service and callers that build the command.
Why: a command is one frozen value, so a service receives its input already shaped and unchangeable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import Id, Instant


@dataclass(frozen=True, slots=True)
class CancelRequest:
    """Ask central to cancel an open request.

    What: names the mission, the request, the instant and the reason.
    When called: by RescueCentral.cancel_request, which hands the command to the cancel_request service.
    Why: a request that is no longer wanted must release its seats.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    mission_id: Id
    request_id: Id
    now: Instant
    reason: str
