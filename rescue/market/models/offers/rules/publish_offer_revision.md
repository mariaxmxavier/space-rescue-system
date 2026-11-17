# publish_offer_revision

**Category:** Offers · **Code:** [publish_offer_revision.py](publish_offer_revision.py) ·
**Diagram:** [ShipMarket UML](../../../../../docs/architecture/diagrams/rescue-domain-model/namespaces/ShipMarket/class-diagram.mmd) `Ship` → `ShipOffer` ◆ `ShipOfferRevision`

```python
publish_offer_revision(
    market: B3Market, offer_id: str, revision: ShipOfferRevision,
    *, mission_id: str | None = None, ship_id: str | None = None,
) -> B3Market
```

## What

Appends `revision` to the offer `offer_id`. If the offer does not exist yet, creates it with this
revision as its first, for `mission_id` and `ship_id`. Publishing a revision that is already there,
unchanged, returns the market as it was.

## When

- A ship makes its first offer to a mission, or revises it (the publish-offer-revision operation).
- A simulation scenario changes an offer.

## Why

A seat request pins the exact revision it was made against, so revisions are history and must
never change. The highest `revision_number` is current; `recorded_at` does not order revisions.
One mission and one ship share at most one offer, so its revisions stay in one place.

## Refuses

| Situation | Error |
|---|---|
| `revision` is not a `ShipOfferRevision` | revision must be a ShipOfferRevision value |
| two offers already share `offer_id` | ship offer identity must be unique |
| an existing revision id with different data | revision identity was reused with changed data |
| an existing revision number | revision number was reused |
| a new offer without `mission_id` or `ship_id` | a new ship offer requires mission_id and ship_id |
| the mission and ship already have another offer | mission and ship already have a logical ship offer |

## Example

`offer-1` has revision 1 (6 seats). Publishing revision 2 (4 seats) keeps both;
`current_revision` is revision 2. Publishing another revision numbered 1 is refused.
