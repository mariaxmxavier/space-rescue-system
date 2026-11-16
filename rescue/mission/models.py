"""Immutable values for missions, seat requests, and mission progress."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from rescue.values import (
    DomainValidationError,
    Id,
    Instant,
    immutable_tuple,
    normalize_id,
    normalize_nonnegative_quantity,
    normalize_positive_quantity,
)
from rescue.values import normalize_instant as _normalize_instant_value


_REQUEST_OUTCOMES = frozenset(
    {"pending", "accepted", "partially_accepted", "refused", "cancelled", "expired"}
)
_PROGRESS_STATUSES = frozenset({"complete", "awaiting_responses", "needs_more_help"})


def _normalize_name(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{label} must be a nonblank string")
    return value


def _normalize_instant(value: object) -> Instant:
    """Normalize boundary inputs and preserve already-normalized Decimal instants."""
    if isinstance(value, Decimal):
        return _normalize_instant_value(str(value))
    return _normalize_instant_value(value)


def _optional_id(value: object, label: str) -> Id | None:
    if value is None:
        return None
    try:
        return normalize_id(value)
    except ValueError as error:
        raise DomainValidationError(f"{label} must be a nonblank identifier") from error


def _optional_instant(value: object) -> Instant | None:
    if value is None:
        return None
    return _normalize_instant(value)


def _signed_quantity(value: object, label: str) -> int:
    if type(value) is not int:
        raise DomainValidationError(f"{label} must be an integer")
    return value


def _validate_mission_identity(
    mission_id: object,
    station_name: object,
    people_count: object,
    created_at: object,
) -> tuple[Id, str, int, Instant]:
    return (
        normalize_id(mission_id),
        _normalize_name(station_name, "station name"),
        normalize_positive_quantity(people_count),
        _normalize_instant(created_at),
    )


@dataclass(frozen=True, slots=True)
class MissionData:
    """Registration input; demand is a positive, fixed mission property."""

    mission_id: Id
    station_name: str
    people_count: int
    created_at: Instant

    def __post_init__(self) -> None:
        mission_id, station_name, people_count, created_at = _validate_mission_identity(
            self.mission_id, self.station_name, self.people_count, self.created_at
        )
        object.__setattr__(self, "mission_id", mission_id)
        object.__setattr__(self, "station_name", station_name)
        object.__setattr__(self, "people_count", people_count)
        object.__setattr__(self, "created_at", created_at)


@dataclass(frozen=True, slots=True)
class SeatRequest:
    """A ship's request to confirm a quantity of seats for one mission."""

    request_id: Id
    command_id: Id
    mission_id: Id
    ship_id: Id
    requested_seats: int
    confirmed_seats: int
    outcome: str
    submitted_at: Instant
    response_received_at: Instant | None = None
    response_deadline: Instant | None = None
    closed_at: Instant | None = None
    quote_id: Id | None = None
    revision_id: Id | None = None
    decision_id: Id | None = None

    def __post_init__(self) -> None:
        for field_name in ("request_id", "command_id", "mission_id", "ship_id"):
            object.__setattr__(self, field_name, normalize_id(getattr(self, field_name)))

        object.__setattr__(
            self, "requested_seats", normalize_positive_quantity(self.requested_seats)
        )
        object.__setattr__(
            self, "confirmed_seats", normalize_nonnegative_quantity(self.confirmed_seats)
        )
        if not isinstance(self.outcome, str) or self.outcome not in _REQUEST_OUTCOMES:
            raise DomainValidationError(f"unknown request outcome: {self.outcome!r}")

        submitted_at = _normalize_instant(self.submitted_at)
        object.__setattr__(self, "submitted_at", submitted_at)
        for field_name in ("response_received_at", "response_deadline", "closed_at"):
            instant = _optional_instant(getattr(self, field_name))
            if instant is not None and field_name != "response_deadline" and instant < submitted_at:
                raise DomainValidationError(f"{field_name} cannot precede submission")
            object.__setattr__(self, field_name, instant)
        if self.response_deadline is not None and self.response_deadline <= submitted_at:
            raise DomainValidationError("response deadline must follow request submission")
        if (
            self.response_received_at is not None
            and self.response_deadline is not None
            and self.response_received_at >= self.response_deadline
        ):
            raise DomainValidationError("response received at or after deadline must expire")

        for field_name in ("quote_id", "revision_id", "decision_id"):
            object.__setattr__(
                self,
                field_name,
                _optional_id(getattr(self, field_name), field_name.replace("_", " ")),
            )

        requested = self.requested_seats
        confirmed = self.confirmed_seats
        if self.outcome == "pending" and confirmed != 0:
            raise DomainValidationError("pending request cannot confirm seats")
        if self.outcome == "accepted" and confirmed != requested:
            raise DomainValidationError("accepted request must confirm all requested seats")
        if self.outcome == "partially_accepted" and not 0 < confirmed < requested:
            raise DomainValidationError("partial acceptance must confirm a positive subset")
        if self.outcome in {"refused", "cancelled", "expired"} and confirmed != 0:
            raise DomainValidationError(f"{self.outcome} request cannot confirm seats")
        if self.outcome in {"cancelled", "expired"} and self.response_received_at is not None:
            raise DomainValidationError(
                f"{self.outcome} request cannot invent a response receipt time"
            )


@dataclass(frozen=True, slots=True)
class RequestHistoryEntry:
    """One applied request creation or terminal transition in mission history."""

    event_id: Id
    mission_sequence: int
    recorded_at: Instant
    action: str
    confirmed_seats_delta: int
    pending_seats_delta: int
    reason: str
    message_id: Id | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", normalize_id(self.event_id))
        object.__setattr__(
            self, "mission_sequence", normalize_positive_quantity(self.mission_sequence)
        )
        object.__setattr__(self, "recorded_at", _normalize_instant(self.recorded_at))
        object.__setattr__(self, "action", _normalize_name(self.action, "history action"))
        object.__setattr__(
            self,
            "confirmed_seats_delta",
            _signed_quantity(self.confirmed_seats_delta, "confirmed seats delta"),
        )
        object.__setattr__(
            self,
            "pending_seats_delta",
            _signed_quantity(self.pending_seats_delta, "pending seats delta"),
        )
        object.__setattr__(self, "reason", _normalize_name(self.reason, "history reason"))
        object.__setattr__(self, "message_id", _optional_id(self.message_id, "message id"))


@dataclass(frozen=True, slots=True)
class MissionProgress:
    """Read-only accounting snapshot derived from mission requests."""

    demand: int
    confirmed: int
    pending: int
    unconfirmed: int
    additional_needed: int
    status: str

    def __post_init__(self) -> None:
        demand = normalize_positive_quantity(self.demand)
        confirmed = normalize_nonnegative_quantity(self.confirmed)
        pending = normalize_nonnegative_quantity(self.pending)
        unconfirmed = normalize_nonnegative_quantity(self.unconfirmed)
        additional_needed = normalize_nonnegative_quantity(self.additional_needed)
        if confirmed + pending > demand:
            raise DomainValidationError("confirmed and pending seats exceed mission demand")
        if unconfirmed != demand - confirmed:
            raise DomainValidationError("unconfirmed seats do not match mission accounting")
        if additional_needed != demand - confirmed - pending:
            raise DomainValidationError("additional demand does not match mission accounting")
        expected_status = (
            "complete"
            if confirmed == demand
            else "awaiting_responses"
            if confirmed + pending == demand
            else "needs_more_help"
        )
        if (
            not isinstance(self.status, str)
            or self.status not in _PROGRESS_STATUSES
            or self.status != expected_status
        ):
            raise DomainValidationError(f"invalid mission progress status: {self.status!r}")
        object.__setattr__(self, "demand", demand)
        object.__setattr__(self, "confirmed", confirmed)
        object.__setattr__(self, "pending", pending)
        object.__setattr__(self, "unconfirmed", unconfirmed)
        object.__setattr__(self, "additional_needed", additional_needed)


@dataclass(frozen=True, slots=True)
class RequestTiming:
    """Read-only elapsed-time projection for one immutable request snapshot."""

    submitted_at: Instant
    response_received_at: Instant | None
    waiting_seconds: Instant
    response_elapsed_seconds: Instant | None

    def __post_init__(self) -> None:
        submitted_at = _normalize_instant(self.submitted_at)
        received_at = _optional_instant(self.response_received_at)
        waiting = _normalize_instant(self.waiting_seconds)
        elapsed = _optional_instant(self.response_elapsed_seconds)
        if received_at is None:
            if elapsed is not None:
                raise DomainValidationError("response elapsed time requires a receipt time")
        else:
            if received_at < submitted_at:
                raise DomainValidationError("response receipt cannot precede submission")
            if elapsed != received_at - submitted_at or waiting != 0:
                raise DomainValidationError("response timing projection is inconsistent")
        object.__setattr__(self, "submitted_at", submitted_at)
        object.__setattr__(self, "response_received_at", received_at)
        object.__setattr__(self, "waiting_seconds", waiting)
        object.__setattr__(self, "response_elapsed_seconds", elapsed)


@dataclass(frozen=True, slots=True)
class Mission:
    """Immutable mission aggregate with fixed demand and tuple-owned records."""

    mission_id: Id
    station_name: str
    people_count: int
    created_at: Instant
    requests: tuple[SeatRequest, ...] = ()
    history: tuple[RequestHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        mission_id, station_name, people_count, created_at = _validate_mission_identity(
            self.mission_id, self.station_name, self.people_count, self.created_at
        )
        requests = immutable_tuple(self.requests)
        history = immutable_tuple(self.history)
        if any(not isinstance(request, SeatRequest) for request in requests):
            raise DomainValidationError("mission requests must be SeatRequest values")
        if any(not isinstance(entry, RequestHistoryEntry) for entry in history):
            raise DomainValidationError("mission history must contain RequestHistoryEntry values")
        object.__setattr__(self, "mission_id", mission_id)
        object.__setattr__(self, "station_name", station_name)
        object.__setattr__(self, "people_count", people_count)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "requests", requests)
        object.__setattr__(self, "history", history)
