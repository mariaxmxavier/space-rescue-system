# Feature Specification: A Clear Application Layer

**Feature Branch**: `008-application-conformance`
**Created**: 2026-11-16
**Updated**: 2026-11-17
**Status**: Draft
**Input**: Simplify application only: split Central and application types into nested files,
explain their purpose, follow Cosmic Python and Clean Architecture, and link UML and ER diagrams.

## Scope and Terms

Make `rescue/application/` easy to navigate and understand without changing rescue behaviour.
Here, **conformance** means meeting the named rules below, with automated evidence.

| Term | Meaning in this feature |
|------|-------------------------|
| Business rule | Decides valid rescue behaviour, such as seat limits. Owned by the domain. |
| Use case / service | Coordinates one operation using domain rules and injected dependencies. |
| Command / result contract | Defines use-case input and output data; currently grouped in `contracts.py`. |
| Port | Defines what a service needs from storage, clocks, identity sources, or simulation. |
| Import contract | An automated restriction on which packages may import other packages. |
| UML class diagram | Shows types, responsibilities, and dependencies. |
| ER diagram | Shows data identities, relationships, and cardinalities; it does not require a database. |

Applicable standards: Cosmic Python for focused services and injected ports; Clean Architecture
for inward dependencies and independent business rules; project-setup for the existing pinned
toolchain, test layout, and `make check-all` gates. The repository's
[instructions](../../AGENTS.md), [constitution](../../.specify/memory/constitution.md), and
[roadmap](../../docs/planning/roadmap.md) remain authoritative.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find one operation or type (Priority: P1)

A maintainer can change one use case or application type without reading all of Central.

**Why this priority**: Central mixes many operations, while contracts groups distinct types.

**Independent Test**: Locate each use case and type in its own named file and run focused tests.

**Acceptance Scenarios**:

1. **Given** application code, **When** looking for a use case, command, result, enum, or
   application-owned model, **Then** it has one named file in nested folders grouped by responsibility.
2. **Given** existing callers, **When** using Central, **Then** its public operations still work
   by delegating to focused services; Central contains no use-case logic.
3. **Given** shared orchestration logic, **When** several services need it, **Then** they reuse
   one implementation rather than copying it.

### User Story 2 - Understand the code and diagrams (Priority: P1)

A maintainer can explain what an application unit does, who calls it, and why it exists.

**Why this priority**: Smaller files help only when responsibilities and relationships are clear.

**Independent Test**: Read docstrings and follow their diagram links to the named elements.

**Acceptance Scenarios**:

1. **Given** any application module, class, or function (including private helpers), **When**
   reading its docstring, **Then** it explains `What:`, `When called:`, `Why:`, and `Diagram:`.
2. **Given** an application type or use case, **When** following its UML reference, **Then** its
   responsibilities and dependencies agree with the code; data types also map to the ER view.
3. **Given** a non-obvious constraint, **When** reading its explanation, **Then** it names the
   rule protected or contract followed and references its source.

### User Story 3 - Preserve boundaries and results (Priority: P1)

A maintainer can test an operation without real infrastructure and verify unchanged results.

**Why this priority**: Moving code must preserve transactions, rescue invariants, and caller expectations.

**Independent Test**: Run focused service tests, import checks, the full suite, and the demo.

**Acceptance Scenarios**:

1. **Given** a service with injected fake dependencies, **When** testing its success, rejection,
   and replay paths, **Then** no real I/O is needed.
2. **Given** an import of an adapter implementation, bootstrap, or experiments from application,
   **When** architecture checks run, **Then** they reject it, including function-local imports.
3. **Given** policy comparison, **When** simulation runs through an injected boundary, **Then**
   results remain unchanged without an import cycle.
4. **Given** shared run state, **When** adapters access it, **Then** no application import exception
   is needed; state and experiment values share one deep-immutability implementation.
5. **Given** the completed split, **When** existing behavioural tests and the demo run, **Then**
   assertions, observable outcomes, and demo output remain unchanged.

### Edge Cases

- Repeated command IDs return the original result without allocating seats twice.
- Concurrent operations publish complete states and preserve shared ship capacity.
- Invalid, late, and out-of-order operations preserve accepted state and closed outcomes.
- Compatibility exports must not duplicate type definitions or create import cycles.
- Services are not invented as ER entities: describe them in UML and link the data they coordinate.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Give each application use case a dedicated function or class in its own named file.
  Use nested folders grouped by responsibility. Central MUST only delegate.
- **FR-002**: Give each application-owned class, model, command, result, and enum its own named
  file. Package exports MAY preserve existing imports without duplicating definitions.
- **FR-003**: Every application module, class, and function MUST have the four-part docstring
  described in Story 2. Explain intent and actual callers. Inline comments explain non-obvious
  steps only, rather than narrating every statement.
- **FR-004**: Maintain application UML and ER views linked from the
  [diagram index](../../docs/architecture/diagrams/rescue-domain-model/README.md).
  Map application files to diagram elements and related domain models. Docstring paths MUST
  exist; diagrams MUST agree with implemented types, dependencies, and relationships.
- **FR-005**: Services MUST coordinate domain rules through injected ports and own transaction
  and error handling. They MUST NOT construct concrete adapters or duplicate domain decisions.
  Shared orchestration logic MUST have one implementation.
- **FR-006**: Import contracts MUST restrict application dependencies to domain packages, shared
  inner values, adapter ports, and the standard library. Reject adapter implementations,
  bootstrap, experiments, and import cycles, including function-local imports. Inject simulation.
- **FR-007**: Move `RunState` to an inner home accessible to adapters, remove the temporary
  adapter-to-application exception, and share one deep-immutability implementation.
- **FR-008**: Preserve public operations, result statuses, error reasons, replay semantics,
  transaction guarantees, rescue invariants, and demo output. Adjust test imports where needed
  without weakening behavioural assertions.
- **FR-009**: Test services with fake ports and retain integration tests with in-memory adapters.
  Follow `tests/<type>/<package>/<topic>/`. Enforce layout, docstrings, diagram consistency,
  and import boundaries through the existing check command.

### Key Entities

- **RescueCentral**: the existing public coordinator, retained as a delegating facade.
- **Use case**: one application action with explicit input, output, and dependencies.
- **Command / Result**: plain data crossing a use-case boundary.
- **RunState**: immutable state of a run: missions, market data, and indexes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every application use case and owned type has one named file; no service module
  exceeds 250 lines, and Central contains no use-case logic.
- **SC-002**: All application modules, classes, and functions have the required explanations;
  all diagram links resolve and every owned type has a documented diagram mapping.
- **SC-003**: Architecture checks report zero forbidden imports, zero import cycles, and zero
  adapter-to-application exceptions.
- **SC-004**: Application code reaches at least 95% line and branch coverage, including delegated
  use cases wherever they are placed.
- **SC-005**: `make check-all` passes, existing behavioural assertions are preserved, and demo
  output matches the pre-refactor baseline byte for byte.

## Assumptions

- Scope is application only. Do not split other packages' domain models or introduce new features.
- Specs 002, 003, and 007 are prerequisites per the roadmap. Verify actual merge status before
  implementation; this specification update does not claim they are complete.
- Necessary external edits are limited to moving shared run state/immutability support,
  adjusting callers and wiring, updating diagrams, and enforcing or testing application boundaries.
- Keep the `rescue/application/` package name. Choose its exact nested tree during planning.
- Reuse Spec Kit, current tool versions, and existing quality gates. Repository-wide scaffolding,
  documentation-platform, dependency, or OpenSpec migrations are outside this feature.
- Start from the linked UML/ER index. Add application-specific views where domain diagrams do
  not describe orchestration; preserve domain meaning.
