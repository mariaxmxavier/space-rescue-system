"""Cancel a pending seat request.

What: closes the request as cancelled with the command's reason, or ignores one already closed.
When called: by RescueCentral.cancel_request, which hands it the command, the store and the id source.
Why: a request that is no longer wanted must release its seats.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from rescue.adapters.ports import IdSource, TransactionStore
from rescue.application.contracts import CancelRequest, Result
from rescue.application.contracts.snapshots import RequestSnapshot
from rescue.application.shared.close_pending_request import close_pending_request
from rescue.mission.models import RequestOutcome


def cancel_request(
    command: CancelRequest, *, store: TransactionStore, id_source: IdSource
) -> Result[RequestSnapshot]:
    """Close a pending request as cancelled with the command's reason.

    What: closes the pending request through close_pending_request with outcome CANCELLED, event first, inside one store transaction.
    When called: by RescueCentral.cancel_request in rescue/application/central.py.
    Why: cancelling must release the seats the request holds, and a request already closed is left unchanged.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    return store.transact(
        lambda state: close_pending_request(
            state,
            command.mission_id,
            command.request_id,
            RequestOutcome.CANCELLED,
            command.now,
            command.reason,
            id_source=id_source,
            event_first=True,
        )
    )
