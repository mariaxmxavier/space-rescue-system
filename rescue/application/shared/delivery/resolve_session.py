"""Resolve the session step of one received delivery.

What: for a received delivery takes the command envelope or the default local:<ship> one, accepts it on the session and keeps the verdict; a stale verdict also returns the rejected stale_session Result.
When called: third, by record_response in rescue/application/services/communication/record_response.py.
Why: the default session at the stored version, else 1, changes the session index but never an outcome.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.application.contracts import RecordResponse
from rescue.application.shared.delivery.delivery_context import DeliveryContext
from rescue.application.shared.find_session import find_session
from rescue.application.shared.make_result import make_result
from rescue.communication import rules as communication_rules
from rescue.communication.models import FlowDirection, SessionEnvelope
from rescue.state import RunState
from rescue.values import DomainValidationError


def resolve_session(state: RunState, context: DeliveryContext, command: RecordResponse):
    """Resolve session.

    What: for a received delivery takes the command envelope or the default local:<ship> one, accepts it on the session and keeps the verdict; a stale verdict also returns a rejected stale_session Result.
    When called: third, by record_response in rescue/application/services/communication/record_response.py.
    Why: the default session at the stored version, else 1, changes the session index but never an outcome.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    request = context.request
    envelope = None
    session = None
    verdict = None
    if context.received_at is not None:
        envelope = command.envelope
        if envelope is None:
            default_id = f"local:{'unknown' if request is None else request.ship_id}"
            stored = find_session(state, default_id)
            envelope = SessionEnvelope(
                default_id,
                1 if stored is None else stored.version,
                FlowDirection.INBOUND,
                1 if stored is None else stored.next_inbound,
            )
        if not isinstance(envelope, SessionEnvelope):
            raise DomainValidationError("envelope must be a session envelope")
        session, _gap, verdict = communication_rules.accept_inbound(
            find_session(state, envelope.session_id), envelope
        )
    resolved = replace(context, envelope=envelope, session=session, verdict=verdict)
    if verdict == "stale":
        return resolved, make_result("rejected", reason="stale_session")
    return resolved, None
