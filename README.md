# Space Rescue System

A callable Python model for coordinating rescue seats, preventing shared ship overbooking, and comparing deterministic mobilisation scenarios.

## Run it

Install uv 0.13.8 (pinned; the project refuses any other version) and make. The interpreter is CPython **3.14.10**, pinned in `.python-version` and fetched by uv. The project's one runtime dependency is `ortools==9.15.6755`, used only by the mobilisation solver families; `uv.lock` pins everything it pulls in. From the repository root:

```bash
make install
make check-all
make test-unit
make test-integration
make test-e2e
make test-architecture
uv run python -m rescue.demo
make compare
make compare-trace

uv run pytest tests/unit/market tests/integration/application/market_history tests/architecture/market_layout -q --no-cov
```

`make check-all` runs the format check, lint, the import contracts (the architecture check), and the full test suite with coverage, and stops at the first failure. The per-type targets run one test type alone; the last command runs the market tests only.

The test suite covers mission accounting, shared capacity, concurrent operations, retries, timing, scenario comparison, communication failures, and architecture boundaries. The demo shows demand 10 reaching completion through confirmed seats after partial acceptance, refusal, and further mobilisation.

## Design

- `rescue/mission/` owns mission requests, terminal transitions, progress, timing projections, and applied history.
- `rescue/market/` owns ship availability, offer revisions, RFQs, quote holds, and cross-mission inventory accounting, in six category packages (see Market below).
- `rescue/mobilisation/` owns deterministic selection and its candidate explanations.
- `rescue/communication/` owns immutable logical messages and per-attempt delivery diagnostics.
- `rescue/application/` coordinates these values through `TransactionStore`, `Clock`, and `IdSource` ports. `rescue/adapters/memory.py` supplies the in-memory store; `rescue/bootstrap.py` creates one central and one store per run.
- `rescue/experiments/` executes scenarios in fresh contexts. It uses a finite event budget and seeded randomness; it does not sleep, read live market data, or write to the operational run.

Dependencies point inward. Domain rules do not import application orchestration or storage. The callable API is documented in [`specs/001-rescue-domain-model/contracts/callable-api.md`](specs/001-rescue-domain-model/contracts/callable-api.md), and the entity ownership and associations are in the [data model](specs/001-rescue-domain-model/data-model.md).

## Operational behavior

The in-memory adapter serializes each read or write under one lock. An operation stages immutable replacement state and publishes it only after validation succeeds. A failed request or quote transfer does not publish partial business state.

Request retries are scoped by application run and command ID. An identical normalized payload returns its original result; changed content conflicts. Response identity is scoped by run and message ID. Repeated attempts keep one logical message ID and receive distinct delivery IDs. The first valid pre-deadline response closes the request; later or conflicting deliveries are diagnostics and do not change mission history.

Mission demand is fixed. A mission is complete only when confirmed seats equal demand; pending requests do not count as confirmed. Refusal, cancellation, expiration, and partial acceptance release the unconfirmed pending quantity. A response received at or after its deadline expires the request before processing the response. No request deadline or quote lifetime is invented when none is supplied.

## Selection and capacity

A policy names one of six strategies from a closed set; any other name fails when the policy is built. `earliest_arrival` is the default: it orders ships by absolute estimated arrival, then ship ID. `largest_capacity` is the legacy ordering: it orders by remaining allocatable seats, then arrival, then ship ID. `priority_queue`, `min_cost_flow`, `cp_sat` and `knapsack` are the comparison families. Each has a README with a worked example and its limits under [`rescue/mobilisation/algorithms/`](rescue/mobilisation/algorithms/), and [ADR 0001](docs/architecture/decisions/0001-mobilisation-algorithms.md) records why these are the default and the comparison set. Selection records every candidate and reason without reserving seats. Request creation checks current inventory again.

### Strategy assumptions and availability snapshots

- A decision is taken for one mission from one availability snapshot: one candidate per ship, with its offer revision, its free seats and its optional held quote.
- A ship's arrival is its offer revision's record time plus its arrival estimate. The decision time is the instant the decision is taken.
- A decision proposes seats and reserves nothing. A later availability change is seen by the next decision. It does not alter a recorded decision, which is an immutable value, or any settled request.
- Decisions are per mission. The algorithms do not optimise across missions; fleet-wide allocation is out of scope.
- Held quotes are all or nothing. The knapsack family never splits an offer, so it can cover less demand than the others. Min-cost flow fixes held quotes greedily by arrival before the flow runs. The knapsack shortfall appears as remaining demand in its result step, and min-cost flow's quote choices appear as its quote steps.

Inventory counts held unaccepted quotes, pending requests, and confirmed commitments once across missions. The latest availability snapshot supplies the current total. A capacity reduction preserves existing holds, requests, and confirmations; it exposes a shortfall and blocks new allocations until sufficient capacity is available.

## Comparing the mobilisation algorithms

`make compare` runs the five comparison families (`earliest_arrival`, `priority_queue`, `min_cost_flow`, `cp_sat` and `knapsack`) on five fixed scenarios: splittable demand, tied arrivals, held quotes, insufficient supply and knapsack under-coverage. It prints one table with 25 rows, one per scenario and algorithm, and the columns `scenario`, `algorithm`, `seats_covered`, `last_seat_arrival_s`, `ships_used`, `unused_seats` and `runtime_ms`. An empty last-arrival value means no ship was chosen and prints as `-`.

`make compare-trace` prints the same table after a JSON-lines trace of every algorithm step, with the fields `algorithm`, `step`, `ship_id` and `detail`. The equivalent direct command is `uv run python -m benchmarks.mobilisation.compare [--trace]`. The runtime column is the only machine-dependent value; the other columns are deterministic.

The measured runtimes and the thresholds they were checked against are in the US3 section of [`specs/006-mobilisation-conformance/quickstart.md`](specs/006-mobilisation-conformance/quickstart.md).

## Market

`rescue/market/models/` has six categories, one file per entity: Fleet (`Ship`), Availability (`ShipAvailability`), Procurement (`SeatRFQ`, `RFQStatus`), Quotes (`RFQOffer`, `QuoteStatus`, `QuoteStatusChange`), Offers (`ShipOffer`, `ShipOfferRevision`) and Inventory (`ShipUsage`, `CommitmentSource`). `B3Market` holds them for one run. The diagrams under `docs/architecture/diagrams/rescue-domain-model/namespaces/ShipMarket/` are the source of truth for names and relations, and each rule's docstring names its diagram.

The market never edits the past. It keeps three append-only histories, all plain immutable values:

- availability publications per ship; the one with the latest `recorded_at` is current;
- offer revisions per offer; the highest `revision_number` is current;
- quote status changes: one entry per successful hold, acceptance, rejection or expiry, with its instant and, for an acceptance, the request it became. A refused operation adds no entry. Reading the history returns entries in append order. This history is new; before it, a quote's status was overwritten.

A changed availability is a new publication, not an edit. It changes only what can still be allocated: holds, pending requests and confirmed seats made earlier are kept, as the Selection and capacity section describes, and a reduction exposes a shortfall rather than cancelling them.

Accepting a quote runs the hold-to-commitment transfer and the creation of the pending request inside one `TransactionStore.transact` call. Both appear together or neither does.

Concurrency: the market has no locks and no I/O. `MemoryTransactionStore.transact` takes one lock, runs the operation on the current state, and publishes the returned `RunState` only if the operation returns normally. An exception leaves the previous state in place, so concurrent callers see whole operations only. Strategy assumptions: selection reserves nothing, and capacity is checked again when a request is created.

Tests: `tests/unit/market/` covers rules, statuses, history, refusals and generated capacity sequences checked against an independent ledger; `tests/integration/application/market_history/` covers acceptance atomicity; `tests/architecture/market_layout/` checks the layout and docstrings. The verification record is [`specs/005-market-conformance/validation.md`](specs/005-market-conformance/validation.md).

## Simulation timing

All times are finite Decimal seconds. Requests, responses, availability changes, and expirations use one deterministic timeline. Expiration precedes response delivery at the same instant; horizon-time events are processed before an incomplete run stops. Communication RTT is outbound plus return delay; response elapsed time also includes ship decision delay. Arrival estimates remain separate. Lost responses have no receipt time, and duplicated attempts share their message identity.

For the planned stories and verification record, see [`specs/001-rescue-domain-model/quickstart.md`](specs/001-rescue-domain-model/quickstart.md) and [`specs/001-rescue-domain-model/validation.md`](specs/001-rescue-domain-model/validation.md).
