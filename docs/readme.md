# Documentation

## Context

- [Original problem](context/original-problem.md): exercise requirements and constraints.

## Reference

- [Glossary](reference/glossary.md): shared domain and technical terms.
- [Constitution](../.specify/memory/constitution.md): project principles and governance.
- [Working rules](rules/): coding rules for agents and humans, written by the rulebook skill.
- [ID generation race research](reference/id-generation-race-research.md): verified, cited findings on locks, multiprocessing and free-threaded builds for `SequenceIdSource`.

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
