"""Offer rules: one file per rule, each with a `.md` beside it.

When: imported as `from rescue.market.models.offers.rules import publish_offer_revision`.
Why: callers depend on the category's rules, not on the file each rule lives in.
Diagram: ShipMarket class-diagram.mmd, namespace Offers.
"""

from rescue.market.models.offers.rules.publish_offer_revision import publish_offer_revision

__all__ = ["publish_offer_revision"]
