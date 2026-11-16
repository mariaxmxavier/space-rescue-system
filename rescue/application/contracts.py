"""Transport-neutral commands and result values for RescueCentral."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Generic, TypeVar

from rescue.values import Id, Instant

if TYPE_CHECKING:
    from rescue.experiments.models import RunSnapshot
    from rescue.market.models import RFQOffer, ShipAvailability, ShipOfferRevision

T = TypeVar("T")


class ResultStatus(StrEnum):
    APPLIED = "applied"
    REPLAYED = "replayed"
    REJECTED = "rejected"
    IGNORED = "ignored"


class ErrorReason(StrEnum):
    INVALID_INPUT = "invalid_input"
    UNKNOWN_MISSION = "unknown_mission"
    UNKNOWN_SHIP = "unknown_ship"
    UNKNOWN_REQUEST = "unknown_request"
    UNKNOWN_DECISION = "unknown_decision"
    UNKNOWN_MESSAGE = "unknown_message"
    IDENTITY_CONFLICT = "identity_conflict"
    CLOSED_REQUEST = "closed_request"
    LATE = "late"
    INSUFFICIENT_DEMAND = "insufficient_demand"
    INSUFFICIENT_CAPACITY = "insufficient_capacity"
    UNAVAILABLE = "unavailable"
    EXPIRED_QUOTE = "expired_quote"
    REVISION_CONFLICT = "revision_conflict"


@dataclass(frozen=True, slots=True)
class Result(Generic[T]):
    status: str
    value: T | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {status.value for status in ResultStatus}:
            raise ValueError(f"unknown result status: {self.status!r}")
        if self.reason is not None and self.reason not in {
            reason.value for reason in ErrorReason
        }:
            raise ValueError(f"unknown result reason: {self.reason!r}")


@dataclass(frozen=True, slots=True)
class RegisterMission:
    mission_id: Id
    station_name: str
    people_count: int
    created_at: Instant


@dataclass(frozen=True, slots=True)
class RegisterShip:
    ship_id: Id
    name: str


@dataclass(frozen=True, slots=True)
class PublishAvailability:
    availability: ShipAvailability


@dataclass(frozen=True, slots=True)
class PublishOffer:
    offer_id: Id
    mission_id: Id
    ship_id: Id
    revision: ShipOfferRevision


@dataclass(frozen=True, slots=True)
class RequestQuotes:
    mission_id: Id
    now: Instant
    response_deadline: Instant | None = None


@dataclass(frozen=True, slots=True)
class RecordQuote:
    offer: RFQOffer
    now: Instant


@dataclass(frozen=True, slots=True)
class AcceptQuote:
    command_id: Id
    mission_id: Id
    quote_id: Id
    now: Instant
    response_deadline: Instant | None = None
    decision_id: Id | None = None
    revision_id: Id | None = None


@dataclass(frozen=True, slots=True)
class CreateRequest:
    command_id: Id
    mission_id: Id
    ship_id: Id
    requested_seats: int
    revision_id: Id
    now: Instant
    response_deadline: Instant | None = None
    decision_id: Id | None = None


@dataclass(frozen=True, slots=True)
class RejectQuote:
    quote_id: Id
    now: Instant


@dataclass(frozen=True, slots=True)
class RecordResponse:
    message_id: Id
    delivery_id: Id
    attempt_number: int
    request_id: Id
    outcome: str
    confirmed_seats: int
    sent_at: Instant
    received_at: Instant | None
    communication_rtt_seconds: Instant | None = None


@dataclass(frozen=True, slots=True)
class CancelRequest:
    mission_id: Id
    request_id: Id
    now: Instant
    reason: str


@dataclass(frozen=True, slots=True)
class ExpireRequest:
    mission_id: Id
    request_id: Id
    now: Instant


@dataclass(frozen=True, slots=True)
class Mobilise:
    mission_id: Id
    policy_id: Id
    policy_revision: int
    now: Instant


@dataclass(frozen=True, slots=True)
class ComparePolicies:
    scenario_id: Id
    scenario_revision: int
    policy_keys: tuple[tuple[Id, int], ...]
