"""Reject a held quote and release its seats.

What: closes the held quote as rejected, and refuses an unknown or already closed quote.
When called: by RescueCentral.reject_quote, which hands the RejectQuote command to this service.
Why: a rejected quote stops being a candidate for acceptance.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.adapters.ports import TransactionStore
from rescue.application.contracts import RejectQuote, Result
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.find_quote import find_quote
from rescue.application.shared.make_result import make_result
from rescue.market.models.quotes.rules import close_quote
from rescue.state import RunState
from rescue.values import DomainValidationError, normalize_id


def reject_quote(command: RejectQuote, *, store: TransactionStore) -> Result:
    """Close a held quote as rejected and release its seats.

    What: Find the quote, refuse an unknown one as expired_quote and a non-held one as closed_request, otherwise close it as rejected.
    When called: RescueCentral.reject_quote in rescue/application/central.py.
    Why: A rejected quote stops being a candidate for acceptance. Only a held quote may be rejected, so a closed quote is never closed twice.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def operation(state: RunState):
        """Transaction step of reject_quote.

        What: applies the reject_quote rule to the state it receives and returns the new state with its Result.
        When called: passed to store.transact by reject_quote, which runs it once per call.
        Why: Only a held quote may be rejected, so a closed quote is never closed twice.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        try:
            quote_id = normalize_id(command.quote_id)
            quote = find_quote(state, quote_id)
            if quote is None:
                return state, make_result("rejected", reason="expired_quote")
            if quote.status != "held":
                return state, make_result("rejected", reason="closed_request")
            market = close_quote(state.market, quote_id, "rejected", command.now)
            closed = find_quote(replace(state, market=market), quote_id)
            return replace(state, market=market), make_result("applied", closed)
        except (DomainValidationError, TypeError) as error:
            return state, make_result("rejected", reason=error_reason_for(error))

    return store.transact(operation)
