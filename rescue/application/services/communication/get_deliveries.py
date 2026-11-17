"""Return every delivery attempt recorded for one message.

What: reads the delivery index for the message id and returns its deliveries in order, or rejects an unknown message.
When called: by RescueCentral.get_deliveries, which hands it the message id and the store.
Why: callers audit how a message was delivered without touching the run state.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
"""

from __future__ import annotations

from rescue.adapters.ports import TransactionStore
from rescue.application.contracts import Result
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.make_result import make_result
from rescue.communication.models import MessageDelivery
from rescue.state import RunState
from rescue.values import DomainValidationError, normalize_id


def get_deliveries(
    message_id: str, *, store: TransactionStore
) -> Result[tuple[MessageDelivery, ...]]:
    """Return the recorded deliveries of one message, or reject an unknown message.

    What: normalises the message id, collects the matching deliveries from the delivery index and returns them in recorded order; no match is rejected as unknown_message.
    When called: by RescueCentral.get_deliveries in rescue/application/central.py.
    Why: callers audit how a message was delivered without touching the run state, and a validation error becomes a named rejection.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
    """

    def operation(state: RunState):
        try:
            normalized = normalize_id(message_id)
            deliveries = tuple(
                item[2]
                for item in state.delivery_index
                if isinstance(item, tuple) and len(item) == 3 and item[1] == normalized
            )
            if not deliveries:
                return state, make_result("rejected", reason="unknown_message")
            return state, make_result("applied", deliveries)
        except (DomainValidationError, TypeError) as error:
            return state, make_result("rejected", reason=error_reason_for(error))

    return store.transact(operation)
