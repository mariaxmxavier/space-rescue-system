"""Inventory rules: one file per rule, each with a `.md` beside it.

When: imported as `from rescue.market.models.inventory.rules import usage`.
Why: callers depend on the category's rules, not on the file each rule lives in.
Diagram: ShipMarket class-diagram.mmd, namespace Inventory.
"""

from rescue.market.models.inventory.rules.usage import usage

__all__ = ["usage"]
