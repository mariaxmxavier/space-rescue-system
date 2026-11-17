"""Explicit public operation inventory for the HTTP entrypoint.

What: maps public operation names to their facade method and input contract.
When called: the API validates a requested operation and builds its arguments.
Why: only reviewed application operations are reachable over HTTP.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from rescue.application.contracts import (
    AcceptQuote,
    CancelRequest,
    ComparePolicies,
    CreateRequest,
    ExpireRequest,
    Mobilise,
    PublishAvailability,
    PublishOffer,
    RecordQuote,
    RecordResponse,
    RecoverReports,
    RegisterMission,
    RegisterShip,
    RejectQuote,
    RequestQuotes,
    SynchroniseInbound,
)


@dataclass(frozen=True, slots=True)
class Operation:
    """Describe the accepted arguments of one facade operation."""

    method: str
    command: type | None = None
    scalar_arguments: tuple[str, ...] = ()


OPERATIONS = MappingProxyType(
    {
        "register_mission": Operation("register_mission", RegisterMission),
        "register_ship": Operation("register_ship", RegisterShip),
        "publish_availability": Operation("publish_availability", PublishAvailability),
        "publish_offer": Operation("publish_offer", PublishOffer),
        "request_quotes": Operation("request_quotes", RequestQuotes),
        "record_quote": Operation("record_quote", RecordQuote),
        "accept_quote": Operation("accept_quote", AcceptQuote),
        "create_request": Operation("create_request", CreateRequest),
        "reject_quote": Operation("reject_quote", RejectQuote),
        "expire_quotes": Operation("expire_quotes", scalar_arguments=("now",)),
        "cancel_request": Operation("cancel_request", CancelRequest),
        "expire_request": Operation("expire_request", ExpireRequest),
        "record_response": Operation("record_response", RecordResponse),
        "recover_reports": Operation("recover_reports", RecoverReports),
        "synchronise_inbound": Operation("synchronise_inbound", SynchroniseInbound),
        "get_session": Operation("get_session", scalar_arguments=("session_id",)),
        "get_progress": Operation("get_progress", scalar_arguments=("mission_id", "now")),
        "get_history": Operation("get_history", scalar_arguments=("mission_id",)),
        "get_decision": Operation("get_decision", scalar_arguments=("decision_id",)),
        "get_deliveries": Operation("get_deliveries", scalar_arguments=("message_id",)),
        "compare": Operation("compare", ComparePolicies),
        "mobilise": Operation("mobilise", Mobilise),
    }
)


def operation_for(name: str) -> Operation | None:
    """Return the registered operation, or ``None`` for an unexposed name."""

    return OPERATIONS.get(name)
