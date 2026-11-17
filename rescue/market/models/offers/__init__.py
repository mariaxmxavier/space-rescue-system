"""Offers category: what a ship offered a mission, revision by revision.

When: read by mobilisation to choose ships and by seat requests to pin the revision they used.
Why: offers change; numbered revisions keep every version so a request can say which one it took.
Diagram: ShipMarket class-diagram.mmd, namespace Offers.

Import entities as `from rescue.market.models.offers import ShipOffer` and rules from
`rescue.market.models.offers.rules`.
"""

from rescue.market.models.offers.ship_offer import ShipOffer
from rescue.market.models.offers.ship_offer_revision import ShipOfferRevision

__all__ = ["ShipOffer", "ShipOfferRevision"]
