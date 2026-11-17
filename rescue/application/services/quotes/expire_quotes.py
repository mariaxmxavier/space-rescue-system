"""Expire the held quotes and pending RFQs whose time has passed.

What: closes each held quote at its expiry and marks each pending RFQ expired at its deadline.
When called: by RescueCentral.expire_quotes, which hands the instant to this service.
Why: expired holds must free their seats and stop being offered for acceptance.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.adapters.ports import TransactionStore
from rescue.application.contracts import Result
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.make_result import make_result
from rescue.market.models.quotes.rules import close_quote
from rescue.state import RunState
from rescue.values import DomainValidationError, normalize_instant


def expire_quotes(now, *, store: TransactionStore) -> Result:
    """Close held quotes whose expiry has passed and mark pending RFQs expired at their deadline.

    What: Close every held quote with expires_at at or before the instant, expire every pending RFQ with a passed deadline, and answer the ids of what expired.
    When called: RescueCentral.expire_quotes in rescue/application/central.py.
    Why: Expired holds must free their seats and stop being offered for acceptance. Time only moves forward through the instant the caller passes in, so expiry is deterministic.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def operation(state: RunState):
        """Transaction step of expire_quotes.

        What: applies the expire_quotes rule to the state it receives and returns the new state with its Result.
        When called: passed to store.transact by expire_quotes, which runs it once per call.
        Why: Time only moves forward through the instant the caller passes in, so expiry is deterministic.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        try:
            instant = normalize_instant(now)
            market = state.market
            expired_ids: list[str] = []
            for quote in tuple(market.quotes):
                if quote.status == "held" and quote.expires_at <= instant:
                    market = close_quote(market, quote.offer_id, "expired", instant)
                    expired_ids.append(quote.offer_id)
            updated_rfqs = []
            for rfq in market.rfqs:
                if (
                    rfq.status == "pending"
                    and rfq.response_deadline is not None
                    and rfq.response_deadline <= instant
                ):
                    updated_rfqs.append(replace(rfq, status="expired"))
                    expired_ids.append(rfq.rfq_id)
                else:
                    updated_rfqs.append(rfq)
            market = replace(market, rfqs=tuple(updated_rfqs))
            return replace(state, market=market), make_result("applied", tuple(expired_ids))
        except (DomainValidationError, TypeError) as error:
            return state, make_result("rejected", reason=error_reason_for(error))

    return store.transact(operation)
