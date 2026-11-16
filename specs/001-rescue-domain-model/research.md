# Research: rescue data model architecture

Date: 2026-11-16. Design decisions below are proposals for review, not amendments to the draft spec.

## Runtime and dependencies
Decision: CPython 3.14.10 (the locally installed interpreter), standard library only; unittest for tests. Pin `.python-version` to `3.14.10` and project `requires-python` to `==3.14.10` during implementation. No new package manager or third-party dependency is needed.
Rationale: direct calls and in-memory state meet the constitution; dataclasses, Protocol, Decimal, threading, heapq, random and unittest supply the required mechanisms.
Alternatives: ORM, web server, broker and event store add no required capability here.
Sources: [Python releases](https://www.python.org/downloads/), [dataclasses](https://docs.python.org/3/library/dataclasses.html), [threading locks](https://docs.python.org/3/library/threading.html#lock-objects), [heapq priority queue notes](https://docs.python.org/3/library/heapq.html#priority-queue-implementation-notes). Consult the versioned 3.14 docs when implementing; generic docs can track a newer version.

## Boundaries and consistency
Decision: capability modules for mission rules, market inventory, mobilisation, communication and experiments. Application RescueCentral orchestrates Mission and B3Market through a transaction port owned by the application. One run-scoped in-memory lock serializes all reads and writes; stage immutable replacement state and publish only after all validation succeeds. History and successful command records commit with business state. Delivery diagnostics are separate and may record rejected attempts.
Rationale: cross-mission inventory cannot be protected by per-mission locks alone. No dependency on the GIL; no transport or callbacks inside a transaction.
Alternatives: distributed transactions and per-ship lock ordering are unnecessary; mutation followed by validation risks partial commits.

## Identities and retry scope
Decision: request command key `(application_run_id, command_id)`; logical message key `(application_run_id, message_id)`. Compare normalized complete business payloads, excluding attempt/receipt metadata. Exact command retries return the saved request ID; changed payload gives `identity_conflict`. Successful commands only enter the request index. Every delivery has its own delivery ID and disposition. Unknown or conflicting messages never create applied history.
Rationale: stable retries and distinct deliveries without claiming durable storage. IDs are nonblank, case-sensitive strings, preserved without trimming; reject whitespace-only values.
Alternatives: per-mission command scope could hide cross-mission collisions; using delivery IDs as message identity would double-apply duplicates.

## Time and revision order
Decision: finite nonnegative Decimal seconds from a run epoch; normalize integers and decimal strings, reject bool and float (including NaN/infinity). All supplied instants use this timeline. Expose UTC epoch metadata separately. Availability current = greatest recorded_at; reject conflicting same-ship snapshots at equal timestamps. Offer current = highest positive revision_number; duplicate number with different content is a conflict.
Rationale: exact ties and deterministic simulation without inferred network latency.
Alternatives: floating-point scheduling and wall-clock sleeps make boundary tests unreliable.

## Expiry and capacity
Decision: caller supplies quote expires_at strictly after recorded_at, with no default TTL. At now >= expiry, expire before accepting. Accepted/rejected/expired quotes are terminal. Request deadline is optional and strictly after submission; at receipt >= deadline expire before evaluating response. Capacity reductions preserve allocations, report shortfall and block new allocations. Existing hold transfers may proceed only when the ship has no shortfall and mission demand permits the full quantity.
Rationale: avoids inventing expiry duration and prevents hidden capacity creation. Accepted quote expiry must not release its pending request.
Alternatives: automatic TTL and revoking confirmations lack authorization.

## Direct requests and RFQs
Decision: preserve the conceptual optional quote association: direct requests are allowed against an immutable ShipOfferRevision with the same latest-inventory checks. Quote-backed requests transfer the entire hold; never split it. RFQs ask each eligible ship for min(mission additional demand, currently allocatable ship seats). RFQ issuance does not reserve seats; quote receipt rechecks current inventory before holding.
Rationale: retains existing request semantics while supporting shared RFQ holds. Quotes across ships may temporarily exceed mission demand in total, but accepted pending plus confirmed never does. Unused holds require explicit rejection/expiry.
Alternatives: treating RFQs as holds would count inventory too early; forcing quotes on every request narrows the existing model.

## Reproducibility
Decision: heap order `(instant, priority, scenario_sequence, insertion_sequence)`; priority 0 for expiration, 1 for other events. Process horizon-time events before stopping, with a finite scenario event budget validated on input to prevent infinite zero-delay generation. Seed one run-local Random; script loss, duplication and ship/request-ordinal responses. Deep value-copy baseline state, including indexes and holds; replace run identity, remap scoped keys, and leave operational references untouched.
Rationale: reproducible business results and isolated experiments. Compare business histories excluding run IDs and wall-clock metadata.
Alternatives: real timers, global random generators and shared mutable baselines undermine repeatability.
