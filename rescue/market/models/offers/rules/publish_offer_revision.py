"""Rule `publish_offer_revision` of the Offers category. Documented in publish_offer_revision.md.

When: called by the publish-offer-revision operation and by scenario steps.
Why: revisions are append-only; refusing reused ids or numbers keeps offer history unchanged.
Diagram: ShipMarket class-diagram.mmd, `Ship` --> `ShipOffer` *-- `ShipOfferRevision`.
"""

from __future__ import annotations

from dataclasses import replace

from rescue.market.models.b3_market import B3Market, require_market
from rescue.market.models.offers.ship_offer import ShipOffer
from rescue.market.models.offers.ship_offer_revision import ShipOfferRevision
from rescue.values import DomainValidationError, normalize_id


def publish_offer_revision(
    market: B3Market,
    offer_id: str,
    revision: ShipOfferRevision,
    *,
    mission_id: str | None = None,
    ship_id: str | None = None,
) -> B3Market:
    """Return a market with `revision` appended to offer `offer_id`, creating the offer if new.

    When: a ship revises (or first makes) its offer to a mission.
    Why: re-publishing the same revision is a no-op so retries are safe; a new offer needs its
    mission and ship, and each (mission, ship) pair has at most one offer.
    Diagram: ShipMarket class-diagram.mmd (namespaces/ShipMarket).
    """
    require_market(market)
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
