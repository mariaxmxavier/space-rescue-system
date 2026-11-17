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
```

`make check-all` runs the format check, lint, the import contracts, and the full test suite with coverage, and reports one pass or fail. The per-type targets run one test type alone.

The test suite covers mission accounting, shared capacity, concurrent operations, retries, timing, scenario comparison, communication failures, and architecture boundaries. The demo shows demand 10 reaching completion through confirmed seats after partial acceptance, refusal, and further mobilisation.

## Design

- `rescue/mission/` owns mission requests, terminal transitions, progress, timing projections, and applied history.
- `rescue/market/` owns ship availability, offer revisions, RFQs, quote holds, and cross-mission inventory accounting.
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

Two strategies are available: `earliest_arrival` orders by absolute estimated arrival and ship ID; `largest_capacity` orders by remaining allocatable seats, then absolute arrival and ship ID. Selection records every candidate and reason without reserving seats. Request creation checks current inventory again.

Inventory counts held unaccepted quotes, pending requests, and confirmed commitments once across missions. The latest availability snapshot supplies the current total. A capacity reduction preserves existing holds, requests, and confirmations; it exposes a shortfall and blocks new allocations until sufficient capacity is available.

## Simulation timing

All times are finite Decimal seconds. Requests, responses, availability changes, and expirations use one deterministic timeline. Expiration precedes response delivery at the same instant; horizon-time events are processed before an incomplete run stops. Communication RTT is outbound plus return delay; response elapsed time also includes ship decision delay. Arrival estimates remain separate. Lost responses have no receipt time, and duplicated attempts share their message identity.

For the planned stories and verification record, see [`specs/001-rescue-domain-model/quickstart.md`](specs/001-rescue-domain-model/quickstart.md) and [`specs/001-rescue-domain-model/validation.md`](specs/001-rescue-domain-model/validation.md).
