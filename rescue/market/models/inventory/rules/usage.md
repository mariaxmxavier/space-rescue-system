# usage

**Category:** Inventory · **Code:** [usage.py](usage.py) ·
**Diagram:** [ShipMarket UML](../../../../../docs/architecture/diagrams/rescue-domain-model/namespaces/ShipMarket/class-diagram.mmd) `ShipUsage` ⇢ `ShipAvailability`, `RFQOffer`, `CommitmentSource`

```python
usage(market: B3Market, commitments: tuple[CommitmentSource, ...], ship_id: str) -> ShipUsage
```

## What

Counts one ship's seats and returns a `ShipUsage`:

| Field | Meaning |
|---|---|
| `total` | seats in the latest availability (0 if none) |
| `held` | seats of the market's quotes in status `held` for this ship |
| `pending` | `requested_seats` of mission requests with outcome `pending` |
| `confirmed` | `confirmed_seats` of requests with outcome `accepted` or `partially_accepted` |
| `used` | `held + pending + confirmed` |
| `free` | `max(0, total - used)`, or 0 when the ship is unavailable |
| `shortfall` | `max(0, used - total)` |

## When

- Inside `hold_quote`, to check the ship has room.
- When progress is reported and when RFQs are sent.
- When mobilisation ranks ships for a mission.

## Why

This is the only place a seat is counted. Held seats come from the market; pending and confirmed
seats come from the missions. An accepted quote is not `held` any more, so its seats count once,
through the request it became. The market reads missions through the `CommitmentSource`
interface, so it never imports the mission package.

## Refuses

| Situation | Error |
|---|---|
| unknown ship | unknown ship |
| two RFQs share an id | RFQ identity must be unique in a market |
| two quotes share an id | quote identity must be unique in a market |
| a quote points at no RFQ | quote must reference a known RFQ |
| two missions share an id | mission identity must be unique in inventory view |

## Example

Ship with 6 seats, one held quote of 4 seats: `held=4, used=4, free=2`. After the quote is
transferred to a pending request of 4: `held=0, pending=4, used=4, free=2`.
