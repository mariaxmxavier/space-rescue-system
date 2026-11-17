"""Availability rules: one file per rule, each with a `.md` beside it.

When: imported as `from rescue.market.models.availability.rules import latest_availability`.
Why: callers depend on the category's rules, not on the file each rule lives in.
Diagram: ShipMarket class-diagram.mmd, namespace Availability.
"""

from rescue.market.models.availability.rules.latest_availability import latest_availability
from rescue.market.models.availability.rules.publish_availability import publish_availability

__all__ = ["latest_availability", "publish_availability"]
