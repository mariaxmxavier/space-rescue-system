"""QuoteStatusChange entity of the Quotes category: one entry of a quote's history.

When: appended to `B3Market.quote_history` by every successful hold, transfer and close.
Why: a quote's status is overwritten in place; this append-only log keeps every earlier state,
so anyone can see when and why seats were held, committed or released.
Diagram: ShipMarket class-diagram.mmd `QuoteStatusChange`; ER `QuoteStatusChange`.
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.market.models.named_value import parse_named
from rescue.market.models.quotes.quote_status import QuoteStatus
from rescue.values import DomainValidationError, Id, Instant, normalize_id, normalize_instant


@dataclass(frozen=True, slots=True)
class QuoteStatusChange:
    """The status a quote moved to, the instant it did, and the request it became (if accepted).

    When: written only by the quote rules, never by callers.
    Why: refused operations write nothing, so the log holds only what really happened.
    Diagrams: ShipMarket class-diagram.mmd and entity-relationship-diagram.mmd.
    """

    quote_id: Id
    status: QuoteStatus
    changed_at: Instant
    request_id: Id | None = None

    def __post_init__(self) -> None:
        """Validate on every construction; only an acceptance names a request."""
        normalize_id(self.quote_id)
        object.__setattr__(self, "status", parse_named(QuoteStatus, self.status, "quote status"))
        object.__setattr__(self, "changed_at", normalize_instant(self.changed_at))
        if self.request_id is not None:
            normalize_id(self.request_id)
        if (self.status is QuoteStatus.ACCEPTED) != (self.request_id is not None):
            raise DomainValidationError("only an accepted quote change names its request")
