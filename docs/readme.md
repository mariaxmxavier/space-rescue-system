# Documentation

## Context

- [Original problem](context/original-problem.md): exercise requirements and constraints.

## Reference

- [Glossary](reference/glossary.md): shared domain and technical terms.
- [Constitution](../.specify/memory/constitution.md): project principles and governance.

## Specifications and Models

- [Rescue domain specification](../specs/001-rescue-domain-model/spec.md): core rules and all six extensions.
- [Domain model diagrams](architecture/diagrams/rescue-domain-model/README.md): Mermaid sources and rendered views.
- [Communication specification](../specs/007-communication-conformance/spec.md): safe delivery decisions, explicit order and maintainability requirements.
- [Communication research](../specs/007-communication-conformance/research.md): B3, exchange protocols, matching algorithms and ordering alternatives.
- [Communication maintainability contract](../specs/007-communication-conformance/contracts/maintainability.md): nested files, explanations, diagram links and checks.
- [Communication plan](../specs/007-communication-conformance/plan.md): layout, delivery waves with parallel tasks, constitution check.
- [Communication data model](../specs/007-communication-conformance/data-model.md) and [design diagrams](../specs/007-communication-conformance/design-diagrams.md): sessions, reports, mission order, components and state machines.
- [Communication quickstart](../specs/007-communication-conformance/quickstart.md): how to verify the feature.

## Architecture decisions

- [Communication ordering](architecture/communication-ordering.md): B3-style session sequencing, per-mission decision ordering, gap handling and recovery examples; implemented on branch 007-communication-conformance.

## Planning

- [Roadmap](planning/roadmap.md): per-package conformance order, specs 002 to 013.
