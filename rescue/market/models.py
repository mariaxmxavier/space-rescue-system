"""Immutable ship-market records and derived inventory values."""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import (
    DomainValidationError,
    Id,
    Instant,
    immutable_tuple,
    normalize_id,
    normalize_instant,
    normalize_nonnegative_quantity,
    normalize_positive_quantity,
)


def _status(value: str, allowed: set[str], field_name: str) -> str:
    if value not in allowed:
        raise DomainValidationError(f"{field_name} must be one of {sorted(allowed)}")
    return value


@dataclass(frozen=True, slots=True)
class Ship:
    ship_id: Id
    name: str

    def __post_init__(self) -> None:
        normalize_id(self.ship_id)
        if not isinstance(self.name, str) or not self.name.strip():
            raise DomainValidationError("ship name must be nonblank")


@dataclass(frozen=True, slots=True)
class ShipAvailability:
    availability_id: Id
    ship_id: Id
    total_seats: int
    arrival_estimate_seconds: Instant
    available: bool
    recorded_at: Instant

    def __post_init__(self) -> None:
        normalize_id(self.availability_id)
        normalize_id(self.ship_id)
        normalize_nonnegative_quantity(self.total_seats)
        object.__setattr__(
            self, "arrival_estimate_seconds", normalize_instant(self.arrival_estimate_seconds)
        )
        object.__setattr__(self, "recorded_at", normalize_instant(self.recorded_at))
        if type(self.available) is not bool:
            raise DomainValidationError("available must be boolean")


@dataclass(frozen=True, slots=True)
class SeatRFQ:
    rfq_id: Id
    mission_id: Id
    ship_id: Id
    availability_id: Id
    requested_seats: int
    status: str
    sent_at: Instant
    response_deadline: Instant | None = None

    def __post_init__(self) -> None:
        for identifier in (self.rfq_id, self.mission_id, self.ship_id, self.availability_id):
            normalize_id(identifier)
        normalize_positive_quantity(self.requested_seats)
        _status(self.status, {"pending", "quoted", "expired"}, "RFQ status")
        object.__setattr__(self, "sent_at", normalize_instant(self.sent_at))
        if self.response_deadline is not None:
            deadline = normalize_instant(self.response_deadline)
            if deadline <= self.sent_at:
                raise DomainValidationError("RFQ response deadline must follow sent_at")
            object.__setattr__(self, "response_deadline", deadline)


@dataclass(frozen=True, slots=True)
class RFQOffer:
    offer_id: Id
    rfq_id: Id
    offered_seats: int
    arrival_estimate_seconds: Instant
    expires_at: Instant
    recorded_at: Instant
    status: str = "held"
    request_id: Id | None = None

    def __post_init__(self) -> None:
        normalize_id(self.offer_id)
        normalize_id(self.rfq_id)
        normalize_positive_quantity(self.offered_seats)
        object.__setattr__(
            self, "arrival_estimate_seconds", normalize_instant(self.arrival_estimate_seconds)
        )
        expiry = normalize_instant(self.expires_at)
        recorded = normalize_instant(self.recorded_at)
        if expiry <= recorded:
            raise DomainValidationError("quote expiry must follow its recorded time")
        object.__setattr__(self, "expires_at", expiry)
        object.__setattr__(self, "recorded_at", recorded)
        _status(self.status, {"held", "accepted", "rejected", "expired"}, "quote status")
        if self.request_id is not None:
            normalize_id(self.request_id)
        if (self.status == "accepted") != (self.request_id is not None):
            raise DomainValidationError("accepted quotes require one linked request")


@dataclass(frozen=True, slots=True)
class ShipOfferRevision:
    revision_id: Id
    revision_number: int
    capacity: int
    arrival_estimate_seconds: Instant
    available: bool
    recorded_at: Instant

    def __post_init__(self) -> None:
        normalize_id(self.revision_id)
        normalize_positive_quantity(self.revision_number)
        normalize_positive_quantity(self.capacity)
        object.__setattr__(
            self, "arrival_estimate_seconds", normalize_instant(self.arrival_estimate_seconds)
        )
        object.__setattr__(self, "recorded_at", normalize_instant(self.recorded_at))
        if type(self.available) is not bool:
            raise DomainValidationError("available must be boolean")


@dataclass(frozen=True, slots=True)
class ShipOffer:
    offer_id: Id
    mission_id: Id
    ship_id: Id
    revisions: tuple[ShipOfferRevision, ...]

    def __post_init__(self) -> None:
        normalize_id(self.offer_id)
        normalize_id(self.mission_id)
        normalize_id(self.ship_id)
        revisions = immutable_tuple(self.revisions)
        if not revisions:
            raise DomainValidationError("ship offer requires at least one revision")
        numbers = [revision.revision_number for revision in revisions]
        if len(numbers) != len(set(numbers)):
            raise DomainValidationError("ship offer revision numbers must be unique")
        object.__setattr__(self, "revisions", revisions)

    @property
    def current_revision(self) -> ShipOfferRevision:
        return max(self.revisions, key=lambda revision: revision.revision_number)


@dataclass(frozen=True, slots=True)
class B3Market:
    market_id: Id
    ships: tuple[Ship, ...] = ()
    availabilities: tuple[ShipAvailability, ...] = ()
    rfqs: tuple[SeatRFQ, ...] = ()
    quotes: tuple[RFQOffer, ...] = ()
    offers: tuple[ShipOffer, ...] = ()

    def __post_init__(self) -> None:
        normalize_id(self.market_id)
        for field_name in ("ships", "availabilities", "rfqs", "quotes", "offers"):
            values = immutable_tuple(getattr(self, field_name))
            object.__setattr__(self, field_name, values)


@dataclass(frozen=True, slots=True)
class ShipUsage:
    total: int
    held: int
    pending: int
    confirmed: int
    used: int
    free: int
    shortfall: int

    def __post_init__(self) -> None:
        for field_name in (
            "total", "held", "pending", "confirmed", "used", "free", "shortfall"
        ):
            normalize_nonnegative_quantity(getattr(self, field_name))
