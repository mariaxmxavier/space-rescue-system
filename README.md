# Space Rescue System

A callable Python model for coordinating rescue seats, preventing shared ship overbooking, and comparing deterministic mobilisation scenarios.

## Run it

Install uv 0.13.8 (pinned; the project refuses any other version) and make. The interpreter is CPython **3.14.10**, pinned in `.python-version` and fetched by uv. The project has no runtime dependencies. From the repository root:

```bash
make install
make check-all
make test-unit
make test-integration
make test-e2e
make test-architecture
uv run python -m rescue.demo
uv run pytest tests/unit/market tests/integration/application/market_history tests/architecture/market_layout -q --no-cov
```

`make check-all` runs the format check, lint, the import contracts (the architecture check), and the full test suite with coverage, and stops at the first failure. The per-type targets run one test type alone; the last command runs the market tests only.

The test suite covers mission accounting, shared capacity, concurrent operations, retries, timing, scenario comparison, communication failures, and architecture boundaries. The demo shows demand 10 reaching completion through confirmed seats after partial acceptance, refusal, and further mobilisation.

## Design

- `rescue/mission/` owns mission requests, terminal transitions, progress, timing projections, and applied history.
- `rescue/market/` owns ship availability, offer revisions, RFQs, quote holds, and cross-mission inventory accounting, in six category packages (see Market below).
- `rescue/mobilisation/` owns deterministic selection and its candidate explanations.
- `rescue/communication/` owns immutable logical messages and per-attempt delivery diagnostics.
- `rescue/application/` coordinates these values through the `TransactionStore`, `Clock`, and `IdSource` ports. The ports are abstract classes in `rescue/adapters/ports/`; `rescue/adapters/memory/` supplies the in-memory store, clock and ID source; `rescue/bootstrap.py` builds one store and one central per run, plus `ZeroClock` and `SequenceIdSource` unless the caller supplies its own clock or ID source.
- `rescue/experiments/` executes scenarios in fresh contexts. It uses a finite event budget and seeded randomness; it does not sleep, read live market data, or write to the operational run.

Dependencies point inward. Domain rules do not import application orchestration or storage. The callable API is documented in [`specs/001-rescue-domain-model/contracts/callable-api.md`](specs/001-rescue-domain-model/contracts/callable-api.md), and the entity ownership and associations are in the [data model](specs/001-rescue-domain-model/data-model.md). Spec 003 replaced the port `Protocol`s described there with the abstract classes in [`specs/003-adapters-conformance/data-model.md`](specs/003-adapters-conformance/data-model.md).

## Operational behavior

Simultaneous requests run in parallel. The in-memory adapter runs each operation on a snapshot without holding a lock, then publishes the result only if no other request committed first: it compares a version number under a short lock. If another commit came first, the operation runs again on the newer state, so no update is lost. A read-only operation publishes nothing and never causes a retry. An operation that raises or returns an invalid state publishes nothing, so a failed request or quote transfer does not publish partial business state. The timelines are in [`docs/architecture/diagrams/store-optimistic-commit.md`](docs/architecture/diagrams/store-optimistic-commit.md).

Request retries are scoped by application run and command ID. An identical normalized payload returns its original result; changed content conflicts. Response identity is scoped by run and message ID. Repeated attempts keep one logical message ID and receive distinct delivery IDs. The first valid pre-deadline response closes the request; later or conflicting deliveries are diagnostics and do not change mission history.

Mission demand is fixed. A mission is complete only when confirmed seats equal demand; pending requests do not count as confirmed. Refusal, cancellation, expiration, and partial acceptance release the unconfirmed pending quantity. A response received at or after its deadline expires the request before processing the response. No request deadline or quote lifetime is invented when none is supplied.

## Selection and capacity

Two strategies are available: `earliest_arrival` orders by absolute estimated arrival and ship ID; `largest_capacity` orders by remaining allocatable seats, then absolute arrival and ship ID. Selection records every candidate and reason without reserving seats. Request creation checks current inventory again.

Inventory counts held unaccepted quotes, pending requests, and confirmed commitments once across missions. The latest availability snapshot supplies the current total. A capacity reduction preserves existing holds, requests, and confirmations; it exposes a shortfall and blocks new allocations until sufficient capacity is available.

## Market

`rescue/market/models/` has six categories, one file per entity: Fleet (`Ship`), Availability (`ShipAvailability`), Procurement (`SeatRFQ`, `RFQStatus`), Quotes (`RFQOffer`, `QuoteStatus`, `QuoteStatusChange`), Offers (`ShipOffer`, `ShipOfferRevision`) and Inventory (`ShipUsage`, `CommitmentSource`). `B3Market` holds them for one run. The diagrams under `docs/architecture/diagrams/rescue-domain-model/namespaces/ShipMarket/` are the source of truth for names and relations, and each rule's docstring names its diagram.

The market never edits the past. It keeps three append-only histories, all plain immutable values:

- availability publications per ship; the one with the latest `recorded_at` is current;
- offer revisions per offer; the highest `revision_number` is current;
- quote status changes: one entry per successful hold, acceptance, rejection or expiry, with its instant and, for an acceptance, the request it became. A refused operation adds no entry. Reading the history returns entries in append order. This history is new; before it, a quote's status was overwritten.

A changed availability is a new publication, not an edit. It changes only what can still be allocated: holds, pending requests and confirmed seats made earlier are kept, as the Selection and capacity section describes, and a reduction exposes a shortfall rather than cancelling them.

Accepting a quote runs the hold-to-commitment transfer and the creation of the pending request inside one `TransactionStore.transact` call. Both appear together or neither does.

Concurrency: the market has no locks and no I/O. `MemoryTransactionStore.transact` runs each operation on a snapshot and publishes the returned `RunState` only if no other commit came first (see Operational behavior). An exception publishes nothing, so concurrent callers see whole operations only. Strategy assumptions: selection reserves nothing, and capacity is checked again when a request is created.

Tests: `tests/unit/market/` covers rules, statuses, history, refusals and generated capacity sequences checked against an independent ledger; `tests/integration/application/market_history/` covers acceptance atomicity; `tests/architecture/market_layout/` checks the layout and docstrings. The verification record is [`specs/005-market-conformance/validation.md`](specs/005-market-conformance/validation.md).

## Simulation timing

All times are finite Decimal seconds. Requests, responses, availability changes, and expirations use one deterministic timeline. Expiration precedes response delivery at the same instant; horizon-time events are processed before an incomplete run stops. Communication RTT is outbound plus return delay; response elapsed time also includes ship decision delay. Arrival estimates remain separate. Lost responses have no receipt time, and duplicated attempts share their message identity.

For the planned stories and verification record, see [`specs/001-rescue-domain-model/quickstart.md`](specs/001-rescue-domain-model/quickstart.md) and [`specs/001-rescue-domain-model/validation.md`](specs/001-rescue-domain-model/validation.md).

## Assumptions

- Time is simulated. All times are finite decimal seconds on one deterministic timeline. There are no real timers: cancellation and expiration are scripted events.
- Each run is isolated: its own in-memory state, its own ID sequence and its own market. The fleet shared across missions is outside the scope of the exercise.
- Mission demand is fixed. Pending requests do not count as confirmed, and a mission is complete only when confirmed seats equal demand.
- Selection reserves nothing. A request is checked against current inventory when it is created.
- A response at or after its deadline expires the request before the response is processed. No deadline or quote lifetime is invented when none is supplied.
- A retry with the same normalized payload returns the original result. Changed content is a conflict.
- Simultaneous requests run in parallel. An operation that conflicts with another commit runs again on the newer state, so operations must have no effect beyond drawing unique IDs.
- Communication loss and delay come from scripted profiles, so every run is reproducible.
- Persistence is in memory only. The demo uses a fixed seed (29) and scripted ship responses, so its output is deterministic.
