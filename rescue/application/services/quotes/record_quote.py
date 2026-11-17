"""Record a quoted offer and hold its seats.

What: checks the quote answers a known RFQ, then holds the quote in the market.
When called: by RescueCentral.record_quote, which hands the RecordQuote command to this service.
Why: an accepted quote must come from a recorded quote.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.adapters.ports import TransactionStore
from rescue.application.contracts import RecordQuote, Result
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.find_rfq import find_rfq
from rescue.application.shared.make_result import make_result
from rescue.market.models.quotes import RFQOffer
from rescue.market.models.quotes.rules import hold_quote
from rescue.state import RunState
from rescue.values import DomainValidationError, normalize_instant


def record_quote(command: RecordQuote, *, store: TransactionStore) -> Result:
    """Record a quoted offer for a known RFQ and hold its seats.

    What: Check the offer is an RFQOffer answering a known RFQ, then hold the quote in the market at the given instant.
    When called: RescueCentral.record_quote in rescue/application/central.py.
    Why: An accepted quote must come from a recorded quote. A quote for an unknown RFQ is invalid_input, so no seats are held for something nobody asked.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def operation(state: RunState):
        """Transaction step of record_quote.

        What: applies the record_quote rule to the state it receives and returns the new state with its Result.
        When called: passed to store.transact by record_quote, which runs it once per call.
        Why: A quote for an unknown RFQ is invalid_input, so no seats are held for something nobody asked.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        try:
            quote = command.offer
            if not isinstance(quote, RFQOffer):
                raise DomainValidationError("offer must be an RFQOffer")
            rfq = find_rfq(state, quote.rfq_id)
            if rfq is None:
                return state, make_result("rejected", reason="invalid_input")
            now = normalize_instant(command.now)
            market = hold_quote(state.market, state.missions, quote, now)
            return replace(state, market=market), make_result("applied", quote)
        except (DomainValidationError, TypeError) as error:
            return state, make_result("rejected", reason=error_reason_for(error))

    return store.transact(operation)
