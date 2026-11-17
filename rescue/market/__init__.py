"""Ship market: where rescue missions get seats on ships without any seat counted twice.

The market has six categories, one folder each under `models/`:

- `fleet`: which ships exist (Ship).
- `availability`: how many seats a ship has now (ShipAvailability).
- `procurement`: which mission asked which ship for seats (SeatRFQ, RFQStatus).
- `quotes`: seats held for a mission and what happened to the hold
  (RFQOffer, QuoteStatus, QuoteStatusChange).
- `offers`: what a ship offered a mission, revision by revision (ShipOffer, ShipOfferRevision).
- `inventory`: how full a ship is (ShipUsage, CommitmentSource, CommitmentRequest).

`B3Market` (`models/b3_market.py`) holds them all for one run. Import entities from their
category package and rules from `models/<category>/rules/`, where each rule has its own file and
a `.md` beside it.

When: imported by the application layer, which runs every market change inside one transaction.
Why: the market owns cross-mission seat safety, so it stands alone and imports only
`rescue.values` (contract `market-standalone`).
Diagrams: docs/architecture/diagrams/rescue-domain-model/namespaces/ShipMarket/
class-diagram.mmd (UML) and entity-relationship-diagram.mmd (ER).
"""
