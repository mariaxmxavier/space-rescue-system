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

- [Web app specification](../specs/013-web-app/spec.md): complete browser operation and inspection scope; [quickstart](../specs/013-web-app/quickstart.md), [validation](../specs/013-web-app/validation.md), [design inputs](../specs/013-web-app/design-inputs.md) and [quality checklist](../specs/013-web-app/checklists/requirements.md).

- [Rescue domain specification](../specs/001-rescue-domain-model/spec.md): core rules and all six extensions.
- [Application specification](../specs/008-application-conformance/spec.md): focused use cases, nested files, explanations, and diagram links.
- Composed mission simulations: [specification](../specs/012-simulations/spec.md), [quality checklist](../specs/012-simulations/checklists/requirements.md), [plan](../specs/012-simulations/plan.md), [research](../specs/012-simulations/research.md), [data model](../specs/012-simulations/data-model.md), [CLI/HTTP contract](../specs/012-simulations/contracts/simulation.md), [full timeline](../specs/012-simulations/contracts/timeline.md), [execution diagram](../specs/012-simulations/design-diagrams.md), [quickstart](../specs/012-simulations/quickstart.md), [parallel tasks](../specs/012-simulations/tasks.md), and [SDD dispatch guide](../specs/012-simulations/execution-handoff.md).
- [Domain model diagrams](architecture/diagrams/rescue-domain-model/README.md): Mermaid sources and rendered views.
- [Communication specification](../specs/007-communication-conformance/spec.md): safe delivery decisions, explicit order and maintainability requirements.
- [Communication research](../specs/007-communication-conformance/research.md): B3, exchange protocols, matching algorithms and ordering alternatives.
- [Communication maintainability contract](../specs/007-communication-conformance/contracts/maintainability.md): nested files, explanations, diagram links and checks.
- [Communication plan](../specs/007-communication-conformance/plan.md): layout, delivery waves with parallel tasks, constitution check.
- [Communication data model](../specs/007-communication-conformance/data-model.md) and [design diagrams](../specs/007-communication-conformance/design-diagrams.md): sessions, reports, mission order, components and state machines.
- [Communication quickstart](../specs/007-communication-conformance/quickstart.md): how to verify the feature.
- [SequenceIdSource race](architecture/diagrams/id-source-race.md): ASCII timelines of the lost update without the lock, and the serialised run with it.
- [Store optimistic commit](architecture/diagrams/store-optimistic-commit.md): ASCII timelines of parallel requests, conflict and retry, and read-only transactions.

## Market rules

Each rule of `rescue/market/` has its own file and a document beside it ([spec 005](../specs/005-market-conformance/spec.md)).

- Availability: [latest_availability](../rescue/market/models/availability/rules/latest_availability.md), [publish_availability](../rescue/market/models/availability/rules/publish_availability.md)
- Procurement: [find_rfq](../rescue/market/models/procurement/rules/find_rfq.md)
- Quotes: [hold_quote](../rescue/market/models/quotes/rules/hold_quote.md), [transfer_quote](../rescue/market/models/quotes/rules/transfer_quote.md), [close_quote](../rescue/market/models/quotes/rules/close_quote.md), [quote_history](../rescue/market/models/quotes/rules/quote_history.md)
- Offers: [publish_offer_revision](../rescue/market/models/offers/rules/publish_offer_revision.md)
- Inventory: [usage](../rescue/market/models/inventory/rules/usage.md)

## Architecture decisions

- [Communication ordering](architecture/communication-ordering.md): B3-style session sequencing, per-mission decision ordering, gap handling and recovery examples; implemented on branch 007-communication-conformance.

## Planning

- [Simulation viewer design](planning/simulation-viewer-design.md): case selection, real execution, paused playback and synchronized timeline seeking.
- [Roadmap](planning/roadmap.md): per-package conformance order, specs 002 to 013.
- Market conformance: [spec](../specs/005-market-conformance/spec.md), [plan](../specs/005-market-conformance/plan.md), [research](../specs/005-market-conformance/research.md), [data model](../specs/005-market-conformance/data-model.md), [contracts](../specs/005-market-conformance/contracts/market.md), [validation guide](../specs/005-market-conformance/quickstart.md), [subagent execution preparation](../specs/005-market-conformance/execution-handoff.md), [validation record](../specs/005-market-conformance/validation.md).
- [Market implementation tasks](../specs/005-market-conformance/tasks.md): story milestones, dependencies and parallel ownership.
# Design drafts

- [Rescue HTTP API design](superpowers/specs/2026-11-17-rescue-http-api-design.md)
- Scripted rescue simulations: [short design](superpowers/specs/2026-11-17-rescue-simulations-design.md) and [flow diagram](superpowers/specs/2026-11-17-rescue-simulations-design-diagram.md).

