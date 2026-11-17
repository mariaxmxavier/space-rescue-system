# Documentation

## Context

- [Original problem](context/original-problem.md): exercise requirements and constraints.

## Reference

- [Glossary](reference/glossary.md): shared domain and technical terms.
- [Constitution](../.specify/memory/constitution.md): project principles and governance.
- [Mobilisation algorithms research](reference/mobilisation-algorithms-research.md): methods and sources behind ADR 0001.

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

## Planning

- [Roadmap](planning/roadmap.md): per-package conformance order, specs 002 to 013.
