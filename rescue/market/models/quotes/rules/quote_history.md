# quote_history

**Category:** Quotes · **Code:** [quote_history.py](quote_history.py) ·
**Diagram:** [ShipMarket UML](../../../../../docs/architecture/diagrams/rescue-domain-model/namespaces/ShipMarket/class-diagram.mmd) `B3Market` → `QuoteStatusChange`

```python
quote_history(market: B3Market, quote_id: str) -> tuple[QuoteStatusChange, ...]
```

## What

Returns every status change of one quote, in append order. Returns an empty
tuple for a quote with no history.

## When

- A maintainer, a report or a test needs to know what happened to a quote and when.

## Why

A quote stores only its current status. `hold_quote`, `transfer_quote` and `close_quote` each add
one `QuoteStatusChange` to `market.quote_history`, and refused operations add none. This rule
reads that append-only log for one quote.

## Refuses

| Situation | Error |
|---|---|
| `market` is not a `B3Market` | market operation requires a B3Market value |

## Example

A quote held at t=2 and accepted at t=4 for `request-1` returns
`(held @2, accepted @4 → request-1)`.
