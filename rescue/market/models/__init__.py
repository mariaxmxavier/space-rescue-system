"""Ship-market models: six category packages and the `B3Market` aggregate.

Import entities from their category (`from rescue.market.models.quotes import RFQOffer`), rules
from the category's rules (`from rescue.market.models.quotes.rules import hold_quote`) and the
aggregate from `rescue.market.models.b3_market`.

When: never imported for its names; it only marks the folder as the market's models layer.
Why: no re-exports, so every caller names the category it depends on and the import graph shows
the market's real structure.
Diagrams: ShipMarket class-diagram.mmd and entity-relationship-diagram.mmd.
"""
