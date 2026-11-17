# Research: market conformance

## Decisions

- Decision: retain six category packages and pure immutable rules. Rationale: roadmap requires conformance in place. Alternative rejected: repository-wide layering or scaffold migration.
- Decision: market owns structural CommitmentSource and CommitmentRequest protocols with read-only properties. Rationale: count real missions without importing their type. Alternative rejected: concrete mission imports violate FR-004; a storage interface is unnecessary here. See Python [Protocol documentation](https://docs.python.org/3.14/library/typing.html#typing.Protocol); annotations do not provide runtime validation.
- Decision: tuples retain availability, offer revision and quote transition histories; existing transactions publish whole RunState replacements. Rationale: acceptance must remove a hold and add pending commitment atomically. Alternatives rejected: in-place mutation and new durable storage.
- Decision: validate string-compatible closed statuses at construction. Rationale: preserve existing callers while rejecting unknown values. Alternative rejected: unrestricted status strings.
- Decision: local seeded Random instances, fixed interpreter and seed/trace failure output. Rationale: replay without new dependencies. See Python [reproducibility notes](https://docs.python.org/3.14/library/random.html#notes-on-reproducibility). Alternative rejected: unseeded randomness or adding a property-testing dependency for this bounded requirement.
- Decision: compare generated steps with an independent ledger. Rationale: usage cannot be its own oracle. Include refusals, holds, transfers, closes and availability changes; use real domain values in pure tests.

## Current implementation assessment

Parallel read-only surveys found much of the requested shape already present, including 200 sequences of 30 steps. No tests were run by the readers.

Remaining assessment priorities:

1. Generated tests use substitute commitment dataclasses; replace them with real domain values to meet no-fakes FR-008. Explicitly assert aggregate/history equality after refusal.
2. Every required class/function needs its own diagram reference; module-level references and the existing When/Why architecture assertions are insufficient.
3. ER currently omits the Inventory representation and explicit six-category grouping; reconcile both diagrams with FR-007.
4. quote_history returns insertion order. Transfer permits event times before the held event; close compares quote creation time. Interpret history as append order, preserving supplied timestamps. Any new timestamp refusal must be a separately justified task reconciled with FR-009, not an incidental behaviour change.
5. The forbidden-import contract lists current siblings. Architecture verification must also protect against type-only imports and future sibling additions.
6. Availability reduction can legitimately produce shortfall; retain commitments and refuse new excess holds rather than asserting used never exceeds reduced capacity.

No technical unknown blocks design. Runtime success, coverage and unchanged demo remain verification obligations.
