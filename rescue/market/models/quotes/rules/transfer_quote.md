# transfer_quote

**Category:** Quotes · **Code:** [transfer_quote.py](transfer_quote.py) ·
**Diagram:** [ShipMarket UML](../../../../../docs/architecture/diagrams/rescue-domain-model/namespaces/ShipMarket/class-diagram.mmd) `RFQOffer` → `QuoteStatusChange`

```python
transfer_quote(market: B3Market, quote_id: str, request_id: str, now: Instant) -> B3Market
```

## What

Marks a held quote `accepted`, links it to the seat request `request_id`, and adds an `accepted`
entry (with the request id) to the quote history.

## When

- The mission accepts a held quote; the application creates a pending seat request for it in
  the same transaction.

## Why

Seats must move from "held" (counted from the market's quotes) to "pending" (counted from the
mission's request) in one step. An accepted quote no longer counts as held, so the seats are
counted exactly once: never twice, never zero.

## Refuses

| Situation | Error |
|---|---|
| the quote is unknown or duplicated | quote identity must resolve exactly once |
| the quote is not `held` | only a held quote can transfer to a request |
| `now` is at or after the quote's expiry | quote is expired |

A refused transfer changes nothing and adds no history entry.

## Example

`quote-1` holds 4 seats (`held=4`). After `transfer_quote(market, "quote-1", "request-1", 3)` and
the pending request of 4: `held=0, pending=4`, `used` unchanged. The history shows `held` then
`accepted (request-1)`.
