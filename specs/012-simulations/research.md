# Research: Composed mission timelines

## Composition and solver lifecycle

**Decision:** situations are reusable recipes in one mission's event timeline. Ship/occurrence selectors bind real request IDs after HTTP results. Built-ins: all12; all11 without concurrency; all10 also without repeated-message delivery; baseline with full confirmations. No powerset generator.
**Rationale:** directly incorporates the maintainer's correction and avoids independent scenario logic for each rule.
**Alternatives considered:** twelve independent demonstrations (wrong scope); a generic workflow engine or all 4096 subsets (unnecessary).

**Decision:** call mobilise, filter value.evaluations where selected=true, then submit each proposed allocation through create_request. Include decision_id and the selected offer revision. Repeat after responses, closures or fleet changes.
**Evidence:** rescue/application/services/mobilisation/mobilise.py stores a decision, not a request. rescue/mobilisation/models/decision.py exposes selected only as a Python property; rescue/api/codec.py serializes dataclass fields, so that property is absent on the wire.
**Alternatives:** direct internal experiments runner and fabricated request quantities both bypass the intended solver/HTTP boundary.

## Required 011 interface repair

**Decision:** make runtime annotation resolution work for the registered nested command types in rescue/api/codec.py, without changing domain behavior. Resolve only explicitly registered trusted types, never arbitrary user-provided imports/eval.
**Evidence:** read-only probe of from_json_value({'availability': {}}, PublishAvailability) fails at get_type_hints with NameError: ShipAvailability. TYPE_CHECKING-only imports similarly affect ShipOfferRevision and SessionEnvelope. Existing HTTP tests do not cover this lifecycle.
**Verification:** add valid nested-payload regression tests for publish_availability, publish_offer and record_response and a proposal-to-create-request round trip before simulation implementation depends on them. Preserve malformed/unknown-field rejection. The fixture was exercised in an isolated Python process with temporary runtime type bindings and reached ten confirmed seats; this is feasibility evidence, not a passing test of the unchanged HTTP API.
**Alternative:** bypassing HTTP is excluded. Runtime imports in every command module would spread a transport concern across application contracts; prefer the narrow codec resolution seam.

## Layering and models

**Decision:** add top-level simulations with models/adapters/services/entrypoints. No imports from rescue. Use strict immutable Pydantic contracts; declare pydantic==2.14.3 directly, matching uv.lock, and reuse httpx==0.28.1. Raw JSON remains inside the adapter. Incoming snapshots may retain unknown API fields at the wire edge, but only reviewed typed projections cross inward.
**Rationale:** Cosmic Python PR-COMPONENT-FIRST, PR-MODELS-OVER-DICTS, BP-INJECT-ADAPTERS and the Clean Architecture dependency rule. Frozen models and forbidden extra internal fields keep event definitions predictable. [Pydantic configuration](https://docs.pydantic.dev/latest/api/config/) documents extra-field and immutability controls.
**Alternatives:** copying rescue dataclasses couples the client to internals; transitive-only dependency declarations hide requirements; a second allocation implementation diverges from the solver.

## Time, failure and concurrent I/O

**Decision:** virtual-time heap ordered by (time, phase, ordinal), explicit request deadlines, no sleeps or timers. Bound profiles by 200 events and time 100. Complete missions still drain declared demonstration events.
**Rationale:** existing experiments code is a behavioral reference only; its early-completion stop would hide late probes.

**Decision:** HTTP phase timeouts connect/pool=2s, read/write=10s; no automatic retries. Two worker threads maximum for the intentional competing-request batch, joined before observing aggregate progress. Use separate adapter-owned clients for workers and close them; normal execution stays sequential.
**Rationale:** [HTTPX timeouts](https://www.python-httpx.org/advanced/timeouts/) distinguish connect/read/write/pool limits; [transports](https://www.python-httpx.org/advanced/transports/) describe retry controls and test transports. A mutation timeout has an unknown outcome and must not be silently repeated. [Python executors](https://docs.python.org/3.14/library/concurrent.futures.html) require explicit lifecycle management; a future timeout does not kill an already running thread. Phase timeouts bound inactivity, not total wall-clock runtime, and this plan makes no hard whole-process deadline claim.
**Alternative:** serial calls cannot demonstrate competing submissions; open-ended concurrency and automatic mutation retries add nondeterminism and hidden side effects.

## Quality gates and dispatch

**Decision:** extend current Makefile/import-linter gates and add >=80% branch coverage per new layer; preserve existing rescue floors. root_packages supports multiple top-level packages in installed import-linter 2.16. Update the architecture test that currently hard-codes sixteen contracts.
**Decision:** freeze contracts first; then [P] adapter, runner and situation writers own disjoint paths. Parent owns shared configuration/initializers; a reviewer verifies each task and the complete diff. Explicit user parallelism overrides SDD's usual sequential-writer default only within the recorded path partitions.
**Alternative:** concurrent shared-file edits or marking a task done solely on an agent report violates repository coordination rules.

No unresolved research questions remain. The codec fix is a required implementation prerequisite, not an unexplained assumption that the current API already works.
