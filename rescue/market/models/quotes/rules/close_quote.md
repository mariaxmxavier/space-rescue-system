# close_quote

**Category:** Quotes · **Code:** [close_quote.py](close_quote.py) ·
**Diagram:** [ShipMarket UML](../../../../../docs/architecture/diagrams/rescue-domain-model/namespaces/ShipMarket/class-diagram.mmd) `RFQOffer` → `QuoteStatusChange`

```python
close_quote(market: B3Market, quote_id: str, status: str, now: Instant) -> B3Market
```

## What

Ends a held quote without a request: its status becomes `rejected` or `expired`, its seats are
released, and the matching entry is added to the quote history.

## When

- `rejected`: the mission declines the quote.
- `expired`: the quote's `expires_at` has passed (expiry sweep, or a late acceptance attempt).

## Why

This is the only way held seats are released without becoming a request. Only a quote still
`held` can be closed, and `expired` only once its time is up, so the released seats are exactly
the ones that were held.

## Refuses

| Situation | Error |
|---|---|
| `status` is not `rejected` or `expired` | an unaccepted quote can only be rejected or expired |
| the quote is unknown or duplicated | quote identity must resolve exactly once |
| the quote is not `held` | only unaccepted held quotes can be closed |
| `expired` before `expires_at` | quote cannot expire before its expiry instant |
| `now` is before the quote was recorded | quote cannot close before it was recorded |

A refused close changes nothing and adds no history entry.

## Example

`quote-1` holds 4 of 6 seats. `close_quote(market, "quote-1", "rejected", 3)` gives
`held=0, free=6`; the history shows `held` then `rejected`.
