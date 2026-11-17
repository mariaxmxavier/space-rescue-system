"""The AcceptQuote command contract.

What: defines the command that accepts a held quote.
When called: imported by RescueCentral.accept_quote, the accept_quote service and callers that build the command.
Why: a command is one frozen value, so a service receives its input already shaped and unchangeable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import Id, Instant


@dataclass(frozen=True, slots=True)
class AcceptQuote:
    """Ask central to accept a quote and turn it into a request.

    What: names the command, mission and quote, with optional deadline, decision id and revision id.
    When called: by RescueCentral.accept_quote, which hands the command to the accept_quote service.
    Why: accepting a quote is the decision that starts a rescue request.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    command_id: Id
    mission_id: Id
    quote_id: Id
    now: Instant
    response_deadline: Instant | None = None
    decision_id: Id | None = None
    revision_id: Id | None = None
