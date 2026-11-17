# hold_quote

**Category:** Quotes · **Code:** [hold_quote.py](hold_quote.py) ·
**Diagram:** [ShipMarket UML](../../../../../docs/architecture/diagrams/rescue-domain-model/namespaces/ShipMarket/class-diagram.mmd) `SeatRFQ` ◆ `RFQOffer` → `QuoteStatusChange`

```python
hold_quote(
    market: B3Market, commitments: tuple[CommitmentSource, ...], quote: RFQOffer, now: Instant,
) -> B3Market
```

## What

Records a ship's answer to an open RFQ. The quote's seats become **held** for the mission, the
RFQ becomes `quoted`, and a `held` entry is added to the quote history.

## When

- The record-quote operation: a ship answers an RFQ it received.

## Why

This is the only way seats become held, so the capacity check lives here once. Before holding,
the rule counts every mission's holds, pending and confirmed seats (`usage`). A hold that does
not fit is refused, so two missions can never hold the same seat.

## Refuses

| Situation | Error |
|---|---|
| `quote` is not an `RFQOffer` | quote must be an RFQOffer value |
| `now` is before the quote was recorded | quote cannot be recorded in the future |
| `now` is at or after the quote's expiry | quote is expired |
| the quote is not a fresh `held` quote | new quote response must be an unaccepted held quote |
| the quote id already exists | quote identity already exists |
| the RFQ is unknown or duplicated | RFQ identity must resolve exactly once |
| the RFQ is not `pending` | RFQ already has a response or is expired |
| more seats than the RFQ asked for | quote exceeds its RFQ quantity |
| the RFQ's availability snapshot is missing, for another ship, or unavailable | RFQ availability snapshot is invalid or unavailable |
| the ship's latest availability is missing or unavailable | ship is currently unavailable |
| commitments already exceed the ship's seats | ship capacity is below existing commitments |
| not enough free seats | insufficient ship capacity for quote hold |

A refused hold changes nothing and adds no history entry.

## Example

Ship with 6 seats and nothing used: a 4-seat quote is held (`held=4, free=2`). A second 4-seat
quote for another mission is refused: only 2 seats are free.
