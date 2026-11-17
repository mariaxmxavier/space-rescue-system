# Documentation

## Context

- [Original problem](context/original-problem.md): exercise requirements and constraints.

## Reference

- [Glossary](reference/glossary.md): shared domain and technical terms.
- [Constitution](../.specify/memory/constitution.md): project principles and governance.
- [Mobilisation algorithms research](reference/mobilisation-algorithms-research.md): methods and sources behind ADR 0001.
- [Working rules](rules/): coding rules for agents and humans, written by the rulebook skill.
- [ID generation race research](reference/id-generation-race-research.md): verified, cited findings on locks, multiprocessing and free-threaded builds for `SequenceIdSource`.

## Decisions

- [ADR 0001: Mobilisation algorithms](architecture/decisions/0001-mobilisation-algorithms.md): why these five algorithms, and which is the default.

## Mobilisation algorithms

- [Mobilisation conformance quickstart](../specs/006-mobilisation-conformance/quickstart.md): the commands, the acceptance record and the US3 timings.
- [Greedy allocators](../rescue/mobilisation/algorithms/greedy/README.md) ([diagram](../rescue/mobilisation/algorithms/greedy/diagram.mmd)): earliest arrival (default) and legacy largest capacity.
- [Priority-queue allocator](../rescue/mobilisation/algorithms/priority_queue/README.md) ([diagram](../rescue/mobilisation/algorithms/priority_queue/diagram.mmd)): a min-heap over arrival and ship ID.
- [Minimum-cost-flow allocator](../rescue/mobilisation/algorithms/min_cost_flow/README.md) ([diagram](../rescue/mobilisation/algorithms/min_cost_flow/diagram.mmd)): seats as flow, with greedy quote preallocation.
- [CP-SAT allocator](../rescue/mobilisation/algorithms/cp_sat/README.md) ([diagram](../rescue/mobilisation/algorithms/cp_sat/diagram.mmd)): staged integer optimisation with ship-id ties.
- [Knapsack allocator](../rescue/mobilisation/algorithms/knapsack/README.md) ([diagram](../rescue/mobilisation/algorithms/knapsack/diagram.mmd)): whole offers only, with the shortfall reported.

## Specifications and Models

- [Rescue domain specification](../specs/001-rescue-domain-model/spec.md): core rules and all six extensions.
- [Domain model diagrams](architecture/diagrams/rescue-domain-model/README.md): Mermaid sources and rendered views.
- [SequenceIdSource race](architecture/diagrams/id-source-race.md): ASCII timelines of the lost update without the lock, and the serialised run with it.
- [Store optimistic commit](architecture/diagrams/store-optimistic-commit.md): ASCII timelines of parallel requests, conflict and retry, and read-only transactions.

## Market rules

Each rule of `rescue/market/` has its own file and a document beside it ([spec 005](../specs/005-market-conformance/spec.md)).

- Availability: [latest_availability](../rescue/market/models/availability/rules/latest_availability.md), [publish_availability](../rescue/market/models/availability/rules/publish_availability.md)
- Procurement: [find_rfq](../rescue/market/models/procurement/rules/find_rfq.md)
- Quotes: [hold_quote](../rescue/market/models/quotes/rules/hold_quote.md), [transfer_quote](../rescue/market/models/quotes/rules/transfer_quote.md), [close_quote](../rescue/market/models/quotes/rules/close_quote.md), [quote_history](../rescue/market/models/quotes/rules/quote_history.md)
- Offers: [publish_offer_revision](../rescue/market/models/offers/rules/publish_offer_revision.md)
- Inventory: [usage](../rescue/market/models/inventory/rules/usage.md)

## Planning

- [Roadmap](planning/roadmap.md): per-package conformance order, specs 002 to 013.
- Market conformance: [spec](../specs/005-market-conformance/spec.md), [plan](../specs/005-market-conformance/plan.md), [research](../specs/005-market-conformance/research.md), [data model](../specs/005-market-conformance/data-model.md), [contracts](../specs/005-market-conformance/contracts/market.md), [validation guide](../specs/005-market-conformance/quickstart.md), [subagent execution preparation](../specs/005-market-conformance/execution-handoff.md), [validation record](../specs/005-market-conformance/validation.md).
- [Market implementation tasks](../specs/005-market-conformance/tasks.md): story milestones, dependencies and parallel ownership.
