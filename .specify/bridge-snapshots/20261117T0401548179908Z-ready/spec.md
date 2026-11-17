# Feature Specification: Market Conformance

**Feature Branch**: `005-market-conformance`

**Created**: 2026-11-16

**Status**: Draft

**Input**: User description: "Simplify the market spec. Define the market in more detail, broken into
categories. Cover persistence and history. Break the models into one file per entity, linked to the
UML and ER diagrams. Every module, class and function says what it does, when it is called and why."

## What the market is

The market is where rescue missions get seats on ships. Ships say how many seats they have; a
mission asks for seats; a ship holds seats for it; the mission accepts or the hold ends. The market
never lets two missions count the same seat.

It has six categories. Each category is one folder with one file per entity.

| Category | Question it answers | Entities | Rules |
|---|---|---|---|
| Fleet | Which ships exist? | Ship | — |
| Availability | How many seats does a ship have right now? | ShipAvailability | publish availability, read the latest |
| Procurement | Which mission asked which ship for seats? | SeatRFQ, RFQStatus | — |
| Quotes | Which seats are held for a mission, and what happened to the hold? | RFQOffer, QuoteStatus, QuoteStatusChange | hold, transfer, close |
| Offers | What did a ship offer a mission, revision by revision? | ShipOffer, ShipOfferRevision | publish a revision |
| Inventory | How full is a ship? | ShipUsage, CommitmentSource | compute usage |

`B3Market` is the aggregate that holds all of the above for one run.

Diagrams (the source of truth for names and relations; the code links to them):

- UML: `docs/architecture/diagrams/rescue-domain-model/namespaces/ShipMarket/class-diagram.mmd`
- ER: `docs/architecture/diagrams/rescue-domain-model/namespaces/ShipMarket/entity-relationship-diagram.mmd`

## History and persistence

**History.** The market never edits the past. It keeps three append-only histories:

- availability publications per ship (the one with the latest `recorded_at` counts);
- offer revisions per offer (the highest `revision_number` counts);
- quote status changes: one entry each time a quote is held, accepted, rejected or expires,
  with the instant it happened and, for an acceptance, the request it became.

The quote history is new. Today a quote's status is overwritten and its earlier states are lost.

**Persistence.** The market is plain immutable values. It does no I/O and knows no store. It is
saved as part of the run state through the existing transaction store, which publishes a new
market only when an operation succeeds. A durable store is out of scope (it belongs to the
adapters spec, 003).

## Clarifications

### Session 2026-11-17

- Q: Which import path do callers outside the market use? → A: entities from their category package (`rescue.market.models.<category>`), rules from the category's rules module (`rescue.market.models.<category>.rules`); the single entry points `rescue.market.models` and `rescue.market.rules` are removed.
- Q: What counts as one rule for the per-rule documents? → A: one rule function; each lives in its own file `models/<category>/rules/<rule>.py` with `<rule>.md` beside it.
- Q: Does the nested layout apply to other packages too? → A: No, to the market only; other packages follow it in their own specs.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - No seat is ever counted twice (Priority: P1)

A maintainer runs the market tests and sees that, across many generated sequences of holds,
transfers, closes and availability changes over several missions and ships, a ship is never
overbooked by the market and each seat is counted once.

**Why this priority**: this is the market's core promise. Eight hand-written examples cover it today.

**Independent Test**: run the market tests alone; they generate at least 200 seeded sequences over
2 missions and 2 ships and check usage after every step.

**Acceptance Scenarios**:

1. **Given** a ship with `A` seats, **When** a hold would push usage past `A`, **Then** it is refused and the market is unchanged.
2. **Given** a held quote, **When** it is transferred to a request, **Then** the ship's usage is unchanged.
3. **Given** a held quote, **When** it is rejected or expires, **Then** only its seats are released.
4. **Given** availability lowered below existing commitments, **When** usage is read, **Then** commitments stay and new holds are refused.

---

### User Story 2 - The market's history can be read back (Priority: P2)

A maintainer can read, for any quote, every status it had and when.

**Why this priority**: an overwritten status hides why seats were released or committed.

**Independent Test**: hold, accept and close quotes; read the quote history; it lists each change in order.

**Acceptance Scenarios**:

1. **Given** a quote that was held then accepted, **When** its history is read, **Then** it shows `held` then `accepted` with the request id.
2. **Given** a refused operation, **When** the history is read, **Then** no entry was added.

---

### User Story 3 - The market stands alone (Priority: P3)

The market depends only on shared values. Statuses are named values, not free strings. Each entity
lives in its own file under its category, and each file says what it is, when it is used and why.

**Independent Test**: the check command passes with a contract that forbids the market from
importing any other `rescue` package except `rescue.values`.

**Acceptance Scenarios**:

1. **Given** the contract, **When** market code refers to a mission type (even for type hints only), **Then** the check fails.
2. **Given** named statuses, **When** an unknown status is supplied, **Then** it is rejected at construction.

### Edge Cases

- Two availability publications for one ship at the same instant with different data: refused.
- A hold transferred or closed after it expired: refused, nothing released twice.
- A ship with no published availability: zero seats for new holds.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Market tests MUST check usage after every step of at least 200 seeded, generated sequences over 2+ missions and 2+ ships.
- **FR-002**: The market MUST record one quote status change per successful hold, transfer and close, and none for a refused operation.
- **FR-003**: RFQ and quote statuses MUST be closed, named values; unknown values MUST be refused.
- **FR-004**: The market MUST import only `rescue.values` and the standard library, enforced by a declared contract.
- **FR-005**: Each entity and status MUST live in its own file under its category folder; each module, class and public function MUST have a docstring saying what it does, when it is called and why, and naming its diagram.
- **FR-005a**: Each rule function MUST live in its own file `models/<category>/rules/<rule>.py` with a `<rule>.md` beside it stating what the rule does, when it is called, why it exists, what it refuses, and its diagram.
- **FR-006**: Callers MUST import entities from their category package (`rescue.market.models.<category>`) and rules from `rescue.market.models.<category>.rules`; `rescue.market.models` and `rescue.market.rules` MUST NOT re-export anything.
- **FR-007**: The ShipMarket UML and ER diagrams MUST show the six categories, the statuses and the quote history.
- **FR-008**: `rescue/market/` MUST reach 100% line and branch coverage with no fakes and no I/O.
- **FR-009**: Behaviour outside the new history MUST be unchanged: the full suite passes and the demo output is identical.

### Key Entities

- **Ship** (Fleet): a ship that can carry rescued people.
- **ShipAvailability** (Availability): a ship's seat count and arrival estimate at an instant.
- **SeatRFQ** (Procurement): a mission's request for seats from one ship, tied to the availability it saw.
- **RFQOffer** (Quotes): seats a ship holds for one RFQ until accepted, rejected or expired.
- **QuoteStatusChange** (Quotes): one entry in a quote's history.
- **ShipOffer / ShipOfferRevision** (Offers): a ship's offer to a mission and its numbered revisions.
- **ShipUsage** (Inventory): held + pending + confirmed seats, free seats and shortfall for one ship.
- **B3Market**: the aggregate holding all of the above.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 200+ generated sequences per run, 0 invariant violations.
- **SC-002**: 0 references to other `rescue` packages (except `rescue.values`) inside `rescue/market/`.
- **SC-003**: 100% line and branch coverage for `rescue/market/`.
- **SC-004**: The full suite passes and the demo output is byte-identical.
- **SC-005**: Every entity has its own file and every market docstring names its diagram.

## Assumptions

- Depends on 002. Independent of 003, 004, 006 and 007.
- Generated sequences use the standard library's seeded random generator; no new dependency.
- The market reads mission commitments through a small structural interface it defines itself.
- Statuses compare equal to their old strings, so callers that pass or compare strings keep working.
