# publish_availability

**Category:** Availability · **Code:** [publish_availability.py](publish_availability.py) ·
**Diagram:** [ShipMarket UML](../../../../../docs/architecture/diagrams/rescue-domain-model/namespaces/ShipMarket/class-diagram.mmd) `B3Market` → `ShipAvailability`

```python
publish_availability(market: B3Market, availability: ShipAvailability) -> B3Market
```

## What

Returns a new market with `availability` appended to `market.availabilities`. Publishing the
exact same value again returns the market unchanged.

## When

- A ship reports how many seats it has (the publish-availability operation).
- A simulation scenario changes a ship's capacity.

## Why

Availability is history: the market never edits or deletes a publication. Appending keeps every
past capacity, and `latest_availability` picks the one that counts. Treating an exact replay as a
no-op makes retries safe.

## Refuses

| Situation | Error |
|---|---|
| `availability` is not a `ShipAvailability` | availability must be a ShipAvailability value |
| the ship is not in the fleet | availability references an unknown ship |
| an existing id with different data | availability identity was reused with changed data |
| another publication for the ship at the same `recorded_at` | conflicting availability at the same recorded_at |

## Example

Publishing `availability-2` (ship-1, 2 seats, t=3) after `availability-1` (6 seats, t=1) gives a
market with both; `latest_availability(market, "ship-1")` is now `availability-2`.
