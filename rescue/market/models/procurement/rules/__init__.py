"""Procurement rules: one file per rule, each with a `.md` beside it.

When: imported as `from rescue.market.models.procurement.rules import find_rfq`.
Why: callers depend on the category's rules, not on the file each rule lives in.
Diagram: ShipMarket class-diagram.mmd, namespace Procurement.
"""

from rescue.market.models.procurement.rules.find_rfq import find_rfq

__all__ = ["find_rfq"]
