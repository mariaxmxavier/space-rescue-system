# latest_availability

**Category:** Availability · **Code:** [latest_availability.py](latest_availability.py) ·
**Diagram:** [ShipMarket UML](../../../../../docs/architecture/diagrams/rescue-domain-model/namespaces/ShipMarket/class-diagram.mmd) `Ship` → `ShipAvailability`

```python
latest_availability(market: B3Market, ship_id: str) -> ShipAvailability | None
```

## What

Returns the ship's availability publication with the latest `recorded_at`, or `None` when the
ship has never published one.

## When

- Before a quote is held: the ship must be available now.
- Before RFQs are sent: only ships whose latest publication is available get one.
- Inside `usage`: the latest publication gives the ship's total seats.

## Why

Capacity changes over time. Every publication is kept as history; this one rule decides which
one counts, so every caller sees the same number.

## Refuses

| Situation | Error |
|---|---|
| `market` is not a `B3Market` | market operation requires a B3Market value |
| ship id is unknown | unknown ship |
| two different publications share the latest `recorded_at` | conflicting availability snapshots share recorded_at |

## Example

Ship `ship-1` published 6 seats at t=1 and 2 seats at t=3: the result is the t=3 publication
(2 seats). The t=1 publication stays in `market.availabilities`.
