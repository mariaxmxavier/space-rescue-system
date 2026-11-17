# Communication maintainability contract

Applies to [spec 007](../spec.md), FR-008-FR-014. This is a planned contract; the current code has not yet been reorganised.

## Responsibilities

- Communication models and classification rules are pure domain code. They receive immutable values and request facts, not application state or repositories.
- Application orchestration looks up facts, invokes the rule, applies mission transitions, and publishes session state and reports atomically. Report recovery reads retained immutable reports and never reapplies mission transitions.
- The transaction adapter owns locking. The ordering rule must not create locks, inspect a real clock or perform I/O.
- Follow cosmic-python and Clean Architecture's inward dependency rules. Retain the domain-first packages and foundation gates required by the roadmap.
- Apply project-setup through the existing `make` commands, pinned tools, test folders and import contracts. A new spine, framework, Pydantic migration or repository-wide tooling migration is outside 007.

## Files and folders

One class or public rule per file; nest by responsibility. The plan must provide the final tree and preserve current public imports, including `rescue.communication.models`.

Suggested groups are messages, deliveries, decisions, vocabulary, sessions, recovery and ordering. A nested folder must group related concepts rather than exist only to repeat a filename. Private cohesive validation helpers may share a private module. Package initialisers expose public names without implementing rules.

This explicit project requirement takes precedence over cosmic-python's general preference against excessive fragmentation.

## Explanations

Every module, class and public callable, including public methods, needs a concise docstring with these labels:

```text
One-line domain summary.

What: what this part represents or decides.
When called: its caller and the moment in the rescue flow.
Why: the invariant or maintenance need it protects.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
```

Private helpers need What and Why. Explain algorithm steps and decision precedence in the rule's docstring. Use focused inline comments when a local detail needs explanation; avoid narrating every assignment or duplicating the docstring.

The communication overview must answer:

1. Why communication is separate from mission accounting.
2. How a ship response becomes a message, a delivery decision and a mission transition.
3. How the selected B3-style idempotent inbound and recoverable outbound session flows differ, and what each guarantees.
4. How the per-mission FIFO decision order follows B3's matching engine, and why it uses arrival time only.
5. How duplicates, identity conflicts, retries, loss, delays and deadline equality are handled.
6. Which code owns each step and where it appears in the UML and ER.

## Diagrams

- [Communication UML](../../../docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd)
- [Communication ER](../../../docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd)
- [Diagram index](../../../docs/architecture/diagrams/rescue-domain-model/README.md)

During implementation, reconcile the diagrams with actual request correlation and RTT fields, add sessions, envelopes, reports and gap controls, and correct the ER title. Update sources and rendered views together. Scope sequence identity by `(run, session, version, direction, sequence)`. A message can be retried under a fresh envelope; immutable message content must not include a fixed session sequence. Rules belong in the UML; only persisted concepts and relationships belong in the ER.

## Verification

- Pure tests: `tests/unit/communication/<topic>/`, without fakes or I/O.
- Wired behavior: `tests/integration/application/communication/` and existing resilience/concurrency suites.
- Structure: `tests/architecture/communication_layout/`, checking file ownership, docstrings and diagram correspondence.
- Session tests: gaps, below-expected duplicates, fresh-sequence retry, replay with original numbers, controls without business numbers, invalid recovery ranges, resume and stale versions.
- Ordering tests: race fixtures for confirmation against confirmation, cancellation against confirmation and expiry against late response; gapless mission numbers; no numbers for replays, duplicates or failed transactions; independent missions.
- Baseline copies: cover inherited message/delivery indices, session counters, mission order numbers and retained reports.
- Run `make install` and `make check-all`; measure communication line and branch coverage separately at 100%.
- Compare the documented demo before and after; expose additional ordering fields through the diagnostics specified by the plan.

The plan must settle default session compatibility, legacy baseline migration, report retention, diagnostics and integration ownership before tasks are generated. Cross-session capacity remains protected by atomic transactions; per-session sequence numbers must not be compared as a global priority. The mission order number is the only cross-session order, and only within one mission.
