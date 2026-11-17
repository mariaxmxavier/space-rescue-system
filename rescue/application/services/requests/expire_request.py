"""Expire a pending seat request whose deadline has passed.

What: closes the request as expired, or rejects the command before its deadline.
When called: by RescueCentral.expire_request, which hands it the command, the store and the id source.
Why: a request left unanswered must close and release its seats, never earlier than agreed.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from rescue.adapters.ports import IdSource, TransactionStore
from rescue.application.contracts import ExpireRequest, Result
from rescue.application.contracts.snapshots import RequestSnapshot
from rescue.application.shared.close_pending_request import close_pending_request
from rescue.application.shared.make_result import make_result
from rescue.mission.models import RequestOutcome, SeatRequest


def _before_deadline(request: SeatRequest, instant) -> Result | None:
    """Reject an expiry attempted before the response deadline.

    What: returns a rejected invalid_input result when the request has no deadline or the instant is earlier than it, otherwise None.
    When called: by expire_request, as the guard passed to close_pending_request.
    Why: a request must never expire earlier than its agreed response deadline.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    if request.response_deadline is None or instant < request.response_deadline:
        return make_result("rejected", reason="invalid_input")
    return None


def expire_request(
    command: ExpireRequest, *, store: TransactionStore, id_source: IdSource
) -> Result[RequestSnapshot]:
    """Close a pending request as expired once its deadline has passed.

    What: closes the pending request through close_pending_request with outcome EXPIRED and reason request_expired, guarded by _before_deadline.
    When called: by RescueCentral.expire_request in rescue/application/central.py.
    Why: an unanswered request must close and release its seats, but never before its response deadline.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    return store.transact(
        lambda state: close_pending_request(
            state,
            command.mission_id,
            command.request_id,
            RequestOutcome.EXPIRED,
            command.now,
            "request_expired",
            id_source=id_source,
            event_first=False,
            guard=_before_deadline,
        )
    )
