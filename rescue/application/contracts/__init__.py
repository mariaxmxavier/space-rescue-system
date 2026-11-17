"""Public surface of the application contracts.

What: re-exports the commands, Result, ResultStatus, ErrorReason and snapshot aliases.
When called: imported by callers that send a command or read a Result.
Why: callers keep one stable import path while each contract lives in its own module.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from rescue.application.contracts.commands.accept_quote import AcceptQuote
from rescue.application.contracts.commands.cancel_request import CancelRequest
from rescue.application.contracts.commands.compare_policies import ComparePolicies
from rescue.application.contracts.commands.create_request import CreateRequest
from rescue.application.contracts.commands.expire_request import ExpireRequest
from rescue.application.contracts.commands.mobilise import Mobilise
from rescue.application.contracts.commands.publish_availability import PublishAvailability
from rescue.application.contracts.commands.publish_offer import PublishOffer
from rescue.application.contracts.commands.record_quote import RecordQuote
from rescue.application.contracts.commands.record_response import RecordResponse
from rescue.application.contracts.commands.recover_reports import RecoverReports
from rescue.application.contracts.commands.register_mission import RegisterMission
from rescue.application.contracts.commands.register_ship import RegisterShip
from rescue.application.contracts.commands.reject_quote import RejectQuote
from rescue.application.contracts.commands.request_quotes import RequestQuotes
from rescue.application.contracts.commands.synchronise_inbound import SynchroniseInbound
from rescue.application.contracts.error_reason import ErrorReason
from rescue.application.contracts.result import Result
from rescue.application.contracts.result_status import ResultStatus
from rescue.application.contracts.snapshots import (
    AvailabilitySnapshot,
    DecisionSnapshot,
    MissionSnapshot,
    OfferSnapshot,
    QuoteSnapshot,
    RequestSnapshot,
    RFQSnapshot,
    ShipSnapshot,
)

__all__ = [
    "AcceptQuote",
    "AvailabilitySnapshot",
    "CancelRequest",
    "ComparePolicies",
    "CreateRequest",
    "DecisionSnapshot",
    "ErrorReason",
    "ExpireRequest",
    "MissionSnapshot",
    "Mobilise",
    "OfferSnapshot",
    "PublishAvailability",
    "PublishOffer",
    "QuoteSnapshot",
    "RFQSnapshot",
    "RecordQuote",
    "RecordResponse",
    "RecoverReports",
    "RegisterMission",
    "RegisterShip",
    "RejectQuote",
    "RequestQuotes",
    "RequestSnapshot",
    "Result",
    "ResultStatus",
    "ShipSnapshot",
    "SynchroniseInbound",
]
