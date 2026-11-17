"""Pure market inventory, availability, and offer revision transitions."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from rescue.market.models import (
    B3Market,
    RFQOffer,
    SeatRFQ,
    ShipAvailability,
    ShipOffer,
    ShipOfferRevision,
    ShipUsage,
)
from rescue.mission.models import RequestOutcome
from rescue.values import DomainValidationError, Instant, normalize_id, normalize_instant

if TYPE_CHECKING:
    from rescue.mission.models import Mission


def _require_market(market: B3Market) -> None:
    if not isinstance(market, B3Market):
        raise DomainValidationError("market operation requires a B3Market value")


def _rfq(market: B3Market, rfq_id: str) -> SeatRFQ:
    matches = [rfq for rfq in market.rfqs if rfq.rfq_id == rfq_id]
    if len(matches) != 1:
        raise DomainValidationError("RFQ identity must resolve exactly once")
    return matches[0]


def latest_availability(market: B3Market, ship_id: str) -> ShipAvailability | None:
    _require_market(market)
    normalized_ship_id = normalize_id(ship_id)
    snapshots = [
        snapshot for snapshot in market.availabilities if snapshot.ship_id == normalized_ship_id
    ]
    if not snapshots:
        if not any(ship.ship_id == normalized_ship_id for ship in market.ships):
            raise DomainValidationError("unknown ship")
        return None
    latest_time = max(snapshot.recorded_at for snapshot in snapshots)
    latest = [snapshot for snapshot in snapshots if snapshot.recorded_at == latest_time]
    if len({snapshot for snapshot in latest}) > 1:
        raise DomainValidationError("conflicting availability snapshots share recorded_at")
    return latest[0]


def usage(market: B3Market, missions: tuple[Mission, ...], ship_id: str) -> ShipUsage:
    _require_market(market)
    normalized_ship_id = normalize_id(ship_id)
    availability = latest_availability(market, normalized_ship_id)
    total = availability.total_seats if availability is not None else 0

    rfq_ships: dict[str, str] = {}
    for rfq in market.rfqs:
        if rfq.rfq_id in rfq_ships:
            raise DomainValidationError("RFQ identity must be unique in a market")
        rfq_ships[rfq.rfq_id] = rfq.ship_id
    seen_quotes: set[str] = set()
    held = 0
    for quote in market.quotes:
        if quote.offer_id in seen_quotes:
            raise DomainValidationError("quote identity must be unique in a market")
        seen_quotes.add(quote.offer_id)
        target_ship = rfq_ships.get(quote.rfq_id)
        if target_ship is None:
            raise DomainValidationError("quote must reference a known RFQ")
        if target_ship == normalized_ship_id and quote.status == "held":
            held += quote.offered_seats

    pending = 0
    confirmed = 0
    seen_missions: set[str] = set()
    for mission in missions:
        if mission.mission_id in seen_missions:
            raise DomainValidationError("mission identity must be unique in inventory view")
        seen_missions.add(mission.mission_id)
        for request in mission.requests:
            if request.ship_id != normalized_ship_id:
                continue
            if request.outcome == RequestOutcome.PENDING:
                pending += request.requested_seats
            elif request.outcome in {RequestOutcome.ACCEPTED, RequestOutcome.PARTIALLY_ACCEPTED}:
                confirmed += request.confirmed_seats

    used = held + pending + confirmed
    shortfall = max(0, used - total)
    free = max(0, total - used)
    if availability is not None and not availability.available:
        free = 0
    return ShipUsage(
        total=total,
        held=held,
        pending=pending,
        confirmed=confirmed,
        used=used,
        free=free,
        shortfall=shortfall,
    )


def publish_availability(market: B3Market, availability: ShipAvailability) -> B3Market:
    _require_market(market)
    if not isinstance(availability, ShipAvailability):
        raise DomainValidationError("availability must be a ShipAvailability value")
    if not any(ship.ship_id == availability.ship_id for ship in market.ships):
        raise DomainValidationError("availability references an unknown ship")
    for existing in market.availabilities:
        if existing.availability_id == availability.availability_id:
            if existing == availability:
                return market
            raise DomainValidationError("availability identity was reused with changed data")
        if (
            existing.ship_id == availability.ship_id
            and existing.recorded_at == availability.recorded_at
            and existing != availability
        ):
            raise DomainValidationError("conflicting availability at the same recorded_at")
    return replace(market, availabilities=(*market.availabilities, availability))


def publish_offer_revision(
    market: B3Market,
    offer_id: str,
    revision: ShipOfferRevision,
    *,
    mission_id: str | None = None,
    ship_id: str | None = None,
) -> B3Market:
    _require_market(market)
    normalized_offer_id = normalize_id(offer_id)
    if not isinstance(revision, ShipOfferRevision):
        raise DomainValidationError("revision must be a ShipOfferRevision value")
    matches = [offer for offer in market.offers if offer.offer_id == normalized_offer_id]
    if len(matches) > 1:
        raise DomainValidationError("ship offer identity must be unique")
    if matches:
        offer = matches[0]
        if any(item.revision_id == revision.revision_id for item in offer.revisions):
            if revision in offer.revisions:
                return market
            raise DomainValidationError("revision identity was reused with changed data")
        if any(item.revision_number == revision.revision_number for item in offer.revisions):
            raise DomainValidationError("revision number was reused")
        updated_offer = replace(offer, revisions=(*offer.revisions, revision))
        return replace(
            market,
            offers=tuple(
                updated_offer if item.offer_id == normalized_offer_id else item
                for item in market.offers
            ),
        )
    if mission_id is None or ship_id is None:
        raise DomainValidationError("a new ship offer requires mission_id and ship_id")
    normalize_id(mission_id)
    normalize_id(ship_id)
    if any(offer.mission_id == mission_id and offer.ship_id == ship_id for offer in market.offers):
        raise DomainValidationError("mission and ship already have a logical ship offer")
    new_offer = ShipOffer(
        offer_id=normalized_offer_id,
        mission_id=mission_id,
        ship_id=ship_id,
        revisions=(revision,),
    )
    return replace(market, offers=(*market.offers, new_offer))


def hold_quote(
    market: B3Market,
    missions: tuple[Mission, ...],
    quote: RFQOffer,
    now: Instant,
) -> B3Market:
    _require_market(market)
    if not isinstance(quote, RFQOffer):
        raise DomainValidationError("quote must be an RFQOffer value")
    instant = normalize_instant(now)
    if instant < quote.recorded_at:
        raise DomainValidationError("quote cannot be recorded in the future")
    if instant >= quote.expires_at:
        raise DomainValidationError("quote is expired")
    if quote.status != "held" or quote.request_id is not None:
        raise DomainValidationError("new quote response must be an unaccepted held quote")
    if any(existing.offer_id == quote.offer_id for existing in market.quotes):
        raise DomainValidationError("quote identity already exists")
    rfq = _rfq(market, quote.rfq_id)
    if rfq.status != "pending":
        raise DomainValidationError("RFQ already has a response or is expired")
    if quote.offered_seats > rfq.requested_seats:
        raise DomainValidationError("quote exceeds its RFQ quantity")
    snapshot = next(
        (item for item in market.availabilities if item.availability_id == rfq.availability_id),
        None,
    )
    if snapshot is None or snapshot.ship_id != rfq.ship_id or not snapshot.available:
        raise DomainValidationError("RFQ availability snapshot is invalid or unavailable")
    latest = latest_availability(market, rfq.ship_id)
    if latest is None or not latest.available:
        raise DomainValidationError("ship is currently unavailable")
    current_usage = usage(market, missions, rfq.ship_id)
    if current_usage.shortfall:
        raise DomainValidationError("ship capacity is below existing commitments")
    if quote.offered_seats > current_usage.free:
        raise DomainValidationError("insufficient ship capacity for quote hold")
    updated_rfq = replace(rfq, status="quoted")
    updated_rfqs = tuple(updated_rfq if item.rfq_id == rfq.rfq_id else item for item in market.rfqs)
    return replace(
        market,
        rfqs=updated_rfqs,
        quotes=(*market.quotes, quote),
    )


def transfer_quote(market: B3Market, quote_id: str, request_id: str, now: Instant) -> B3Market:
    _require_market(market)
    normalized_quote_id = normalize_id(quote_id)
    normalized_request_id = normalize_id(request_id)
    instant = normalize_instant(now)
    matches = [quote for quote in market.quotes if quote.offer_id == normalized_quote_id]
    if len(matches) != 1:
        raise DomainValidationError("quote identity must resolve exactly once")
    quote = matches[0]
    if quote.status != "held":
        raise DomainValidationError("only a held quote can transfer to a request")
    if instant >= quote.expires_at:
        raise DomainValidationError("quote is expired")
    accepted = replace(quote, status="accepted", request_id=normalized_request_id)
    return replace(
        market,
        quotes=tuple(
            accepted if item.offer_id == normalized_quote_id else item for item in market.quotes
        ),
    )


def close_quote(market: B3Market, quote_id: str, status: str, now: Instant) -> B3Market:
    _require_market(market)
    normalized_quote_id = normalize_id(quote_id)
    instant = normalize_instant(now)
    if status not in {"rejected", "expired"}:
        raise DomainValidationError("an unaccepted quote can only be rejected or expired")
    matches = [quote for quote in market.quotes if quote.offer_id == normalized_quote_id]
    if len(matches) != 1:
        raise DomainValidationError("quote identity must resolve exactly once")
    quote = matches[0]
    if quote.status != "held":
        raise DomainValidationError("only unaccepted held quotes can be closed")
    if status == "expired" and instant < quote.expires_at:
        raise DomainValidationError("quote cannot expire before its expiry instant")
    if instant < quote.recorded_at:
        raise DomainValidationError("quote cannot close before it was recorded")
    closed = replace(quote, status=status)
    return replace(
        market,
        quotes=tuple(
            closed if item.offer_id == normalized_quote_id else item for item in market.quotes
        ),
    )
