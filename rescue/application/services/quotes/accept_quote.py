"""Accept a held quote and turn it into a pending seat request.

What: replays a repeated command, refuses unknown, foreign or expired quotes, then opens the request.
When called: by RescueCentral.accept_quote, which hands the AcceptQuote command to this service.
Why: accepting a quote is the decision that starts a rescue request.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.adapters.ports import IdSource, TransactionStore
from rescue.application.contracts import AcceptQuote, Result
from rescue.application.shared.command_entry import command_entry
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.find_quote import find_quote
from rescue.application.shared.find_rfq import find_rfq
from rescue.application.shared.make_result import make_result
from rescue.application.shared.open_request import open_request
from rescue.market.models.quotes.rules import close_quote
from rescue.state import RunState
from rescue.values import DomainValidationError, normalize_id, normalize_instant


def accept_quote(command: AcceptQuote, *, store: TransactionStore, id_source: IdSource) -> Result:
    """Accept a held quote and open the pending seat request it leads to.

    What: Replay an identical earlier command, reject a reused command id with other content, an unknown quote, or a quote of another mission, close an expired quote, otherwise open the request and record the command as accept_quote.
    When called: RescueCentral.accept_quote in rescue/application/central.py.
    Why: Accepting a quote is the decision that starts a rescue request. A command id is idempotent: the same content replays the stored result, different content is an identity_conflict.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def operation(state: RunState):
        """Transaction step of accept_quote.

        What: applies the accept_quote rule to the state it receives and returns the new state with its Result.
        When called: passed to store.transact by accept_quote, which runs it once per call.
        Why: A command id is idempotent: the same content replays the stored result, different content is an identity_conflict.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        try:
            command_id = normalize_id(command.command_id)
            mission_id = normalize_id(command.mission_id)
            quote_id = normalize_id(command.quote_id)
            quote = find_quote(state, quote_id)
            payload_quote = quote_id
            payload = (
                mission_id,
                payload_quote,
                None
                if command.response_deadline is None
                else normalize_instant(command.response_deadline),
                None if command.decision_id is None else normalize_id(command.decision_id),
                None if command.revision_id is None else normalize_id(command.revision_id),
            )
            existing = command_entry(state, command_id)
            if existing is not None:
                if existing[2] == "accept_quote" and existing[3] == payload:
                    return state, make_result("replayed", existing[4])
                return state, make_result("rejected", reason="identity_conflict")
            if quote is None:
                return state, make_result("rejected", reason="expired_quote")
            rfq = find_rfq(state, quote.rfq_id)
            if rfq is None or rfq.mission_id != mission_id:
                return state, make_result("rejected", reason="identity_conflict")
            if quote.expires_at <= normalize_instant(command.now):
                expired_market = close_quote(state.market, quote_id, "expired", command.now)
                return replace(state, market=expired_market), make_result(
                    "rejected", reason="expired_quote"
                )
            result_state, result = open_request(
                state,
                id_source=id_source,
                command_id=command_id,
                mission_id=mission_id,
                ship_id=rfq.ship_id,
                requested_seats=quote.offered_seats,
                revision_id=command.revision_id,
                now=command.now,
                response_deadline=command.response_deadline,
                decision_id=command.decision_id,
                quote=quote,
            )
            if result.status == "applied":
                result_state = replace(
                    result_state,
                    command_index=tuple(
                        (item[0], item[1], "accept_quote", payload, item[4])
                        if isinstance(item, tuple) and len(item) == 5 and item[1] == command_id
                        else item
                        for item in result_state.command_index
                    ),
                )
            return result_state, result
        except (DomainValidationError, TypeError) as error:
            return state, make_result("rejected", reason=error_reason_for(error))

    return store.transact(operation)
