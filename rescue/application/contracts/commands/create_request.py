"""The CreateRequest command contract.

What: defines the command that creates a seat request without a quote.
When called: imported by RescueCentral.create_request, the create_request service and callers that build the command.
Why: a command is one frozen value, so a service receives its input already shaped and unchangeable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import Id, Instant


@dataclass(frozen=True, slots=True)
class CreateRequest:
    """Ask central to create a rescue request for a ship.

    What: names the command, mission, ship, seats and revision, with optional deadline and decision id.
    When called: by RescueCentral.create_request, which hands the command to the create_request service.
    Why: a request commits seats of one ship to one mission.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    command_id: Id
    mission_id: Id
    ship_id: Id
    requested_seats: int
    revision_id: Id
    now: Instant
    response_deadline: Instant | None = None
    decision_id: Id | None = None
