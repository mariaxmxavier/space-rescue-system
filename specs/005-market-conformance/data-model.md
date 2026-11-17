# Market data model

All entities are immutable. IDs, instants, seat counts and estimates retain existing rescue.values validation. UML and ER paths are linked in spec.md.

| Entity | Fields | Relation/invariant |
|---|---|---|
| Ship | ship_id, name | Carrier identity |
| ShipAvailability | availability_id, ship_id, total_seats, arrival_estimate_seconds, available, recorded_at | Ship publication; latest recorded_at wins; conflicting same-time publication refused |
| SeatRFQ | rfq_id, mission_id, ship_id, availability_id, requested_seats, status, sent_at, response_deadline? | Positive requested seats; references observed availability; RFQStatus pending/quoted/expired |
| RFQOffer | offer_id, rfq_id, offered_seats, arrival_estimate_seconds, expires_at, recorded_at, status, request_id? | Positive hold; quote status held/accepted/rejected/expired; acceptance names request |
| QuoteStatusChange | quote_id, status, changed_at, request_id? | Request ID present exactly for acceptance |
| ShipOffer | offer_id, mission_id, ship_id, revisions | Owns immutable revision history |
| ShipOfferRevision | revision_id, revision_number, capacity, arrival_estimate_seconds, available, recorded_at | Highest revision current; old requests retain pinned terms |
| ShipUsage | total, held, pending, confirmed, used, free, shortfall | Derived snapshot |
| B3Market | market_id, ships, availabilities, rfqs, quotes, offers, quote_history | Immutable aggregate, tuple collections |

CommitmentSource exposes mission_id and requests; CommitmentRequest exposes ship_id, requested_seats, confirmed_seats, outcome as read-only properties. These are structural views, not persisted entities.

`used = held + pending + confirmed`; `free = max(0, total - used)` (zero when unavailable); `shortfall = max(0, used - total)`. Missing availability permits no new holds. Duplicate mission identities are refused.

Successful holding appends HELD. A held quote may become ACCEPTED before expiry, REJECTED, or EXPIRED by explicit close processing. Terminal decisions stay closed. Each successful transition appends once. Histories retain insertion order and supplied event instants; past entries are never rewritten. Acceptance transfers held into pending within one run transaction, never into confirmed. Request refusal and partial acceptance release only unconfirmed commitments through existing request rules.
