"""The RejectQuote command contract.

What: defines the command that rejects a held quote.
When called: imported by RescueCentral.reject_quote, the reject_quote service and callers that build the command.
Why: a command is one frozen value, so a service receives its input already shaped and unchangeable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import Id, Instant


@dataclass(frozen=True, slots=True)
class RejectQuote:
    """Ask central to reject a quote.

    What: names the quote and the current instant.
    When called: by RescueCentral.reject_quote, which hands the command to the reject_quote service.
    Why: a rejected quote stops being a candidate for acceptance.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    quote_id: Id
    now: Instant
