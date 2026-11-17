# find_rfq

**Category:** Procurement · **Code:** [find_rfq.py](find_rfq.py) ·
**Diagram:** [ShipMarket UML](../../../../../docs/architecture/diagrams/rescue-domain-model/namespaces/ShipMarket/class-diagram.mmd) `B3Market` → `SeatRFQ`

```python
find_rfq(market: B3Market, rfq_id: str) -> SeatRFQ
```

## What

Returns the single RFQ in the market whose `rfq_id` matches.

## When

- Inside `hold_quote`, to find the RFQ a ship's quote answers.

## Why

A quote reaches its ship only through its RFQ. If the id matched no RFQ or more than one, the
quote could hold seats on the wrong ship, so the rule insists on exactly one.

## Refuses

| Situation | Error |
|---|---|
| no RFQ, or more than one, has `rfq_id` | RFQ identity must resolve exactly once |

## Example

A market with `rfq-1` (mission-1 → ship-1): `find_rfq(market, "rfq-1")` returns it;
`find_rfq(market, "rfq-9")` is refused.
