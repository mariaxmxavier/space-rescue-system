"""The RecordQuote command contract.

What: defines the command that records a quoted offer.
When called: imported by RescueCentral.record_quote, the record_quote service and callers that build the command.
Why: a command is one frozen value, so a service receives its input already shaped and unchangeable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rescue.values import Instant

if TYPE_CHECKING:
    from rescue.market.models.quotes import RFQOffer


@dataclass(frozen=True, slots=True)
class RecordQuote:
    """Ask central to record one quoted offer.

    What: carries the RFQOffer and the current instant.
    When called: by RescueCentral.record_quote, which hands the command to the record_quote service.
    Why: an accepted quote must come from a recorded quote.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    offer: RFQOffer
    now: Instant
