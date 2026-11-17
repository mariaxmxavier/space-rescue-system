"""The RequestQuotes command contract.

What: defines the command that opens requests for quote for a mission.
When called: imported by RescueCentral.request_quotes, the request_quotes service and callers that build the command.
Why: a command is one frozen value, so a service receives its input already shaped and unchangeable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import Id, Instant


@dataclass(frozen=True, slots=True)
class RequestQuotes:
    """Ask central to open a request for quotations for a mission.

    What: names the mission, the current instant and an optional response deadline.
    When called: by RescueCentral.request_quotes, which hands the command to the request_quotes service.
    Why: quotes are solicited from the published offers before any request is created.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    mission_id: Id
    now: Instant
    response_deadline: Instant | None = None
