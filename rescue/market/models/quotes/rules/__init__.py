"""Quote rules: one file per rule, each with a `.md` beside it.

When: imported as `from rescue.market.models.quotes.rules import hold_quote`.
Why: callers depend on the category's rules, not on the file each rule lives in.
Diagram: ShipMarket class-diagram.mmd, namespace Quotes.
"""

from rescue.market.models.quotes.rules.close_quote import close_quote
from rescue.market.models.quotes.rules.hold_quote import hold_quote
from rescue.market.models.quotes.rules.quote_history import quote_history
from rescue.market.models.quotes.rules.transfer_quote import transfer_quote

__all__ = ["close_quote", "hold_quote", "quote_history", "transfer_quote"]
