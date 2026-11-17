# Research: ordering messages in rescue and trading systems

**Researched**: 2026-11-17. **Scope**: spec 007. **Decision**: B3-style session sequencing and recovery for delivery, plus B3-style per-mission FIFO decision ordering (the time half of price/time priority) for competing decisions. The maintainer selected both as the approaches closest to B3's published guidelines; decision ordering was added on 2026-11-17.

## Finding

Financial systems use several kinds of ordering together. There is no single algorithm that replaces all of them. The appropriate choice depends on the state being protected, the number of writers and the recovery guarantee. The sources below establish concrete deployments and documented behavior; they do not establish a market-share ranking or reveal proprietary exchange internals.

| Concern | Question | Typical mechanism |
| --- | --- | --- |
| Matching priority | Which resting offer receives a fill? | Price/time, pro-rata, or product-specific hybrids |
| Protocol delivery | Which messages were received, missed or repeated? | Session identity, sequence numbers, acknowledgements and recovery |
| State transition order | Which competing action takes effect first? | A sequencer and serial application of decisions |
| Replica agreement | Which history survives a server failure? | Replicated log and consensus |
| Causality and time | Could one event have influenced another? | Logical clocks, vector clocks or hybrid logical clocks |

## What B3 publishes

B3's current Binary EntryPoint guidelines are **8.4.2.3**, dated **2026-09-28**. They describe price/time matching, separate incoming/outgoing sequence state and recovery within a session version. Incoming gaps can produce `NotApplied` while higher-numbered requests continue; recovery is an application decision. Outgoing gaps use retransmission. Session sequencing is not proof of one global exchange-wide sequence. Special order facilities can alter ordinary priority. These interface documents do not identify B3's internal consensus algorithm or establish that it uses Lamport clocks. [B3 guidelines, sections 2.1, 4.5.4-4.6.2 and 16.1](https://www.b3.com.br/data/files/69/35/F1/AB/94711A103BBB511AAC094EA8/BinaryEntryPoint-MessageSpecificationGuidelines-8.4.2.3-enUS.pdf).

B3 separately documents PTP-synchronised component timestamps, including gateway receipt and matching-engine processing. Clock synchronisation and sequence ordering solve different problems. The timestamp document describes its October 2024 platform configuration, so its numerical accuracy is not treated here as a newly measured 2026 guarantee. [PUMA timestamps 1.1.0, sections 3.3-3.4](https://www.b3.com.br/data/files/F3/30/BD/D4/E1F87910C2881879AC094EA8/B3-PUMA-Timestamps-1.1.0-enUS.pdf).

## Other verified market examples

- Nasdaq describes price/time priority for its OUCH limit order book. OUCH is an order-entry protocol, not a consensus algorithm. [Nasdaq OUCH](https://classic.nasdaqtrader.com/Trader.aspx?id=ouch).
- Nasdaq's SoupBinTCP sequences server data within a session and permits reconnecting at an expected sequence. Client unsequenced data has different guarantees. Do not infer symmetric delivery guarantees. [Nasdaq SoupBinTCP, section 1.2](https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/soupbintcp.pdf).
- CME documents FIFO, pro-rata and configurable matching variants. Selection depends on the instrument; a proportional allocation policy is not a solution to duplicate delivery or replica agreement. [CME supported algorithms](https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457218479/Supported%2BMatching%2BAlgorithms).
- LMAX publicly identifies Disruptor as part of its exchange technology. Its technical paper describes sequencing and inter-thread event processing. A ring buffer does not by itself provide disk durability or distributed consensus. [LMAX technology](https://www.lmax.com/exchange/technology/), [Disruptor technical paper](https://lmax-exchange.github.io/disruptor/disruptor.html).

## Current solution families and their limits

| Solution | Guarantee and useful setting | Limit for this project |
| --- | --- | --- |
| Central sequencer | One authority assigns positions and serialises competing state changes | One authority is a failure boundary; no replicated durability is implied |
| Session sequence and recovery | Identifies gaps and repeated transport messages within a defined session/flow | Does not replace business idempotency or a central cross-session decision order |
| Lamport clock plus process tie-breaker | Extends causal precedence into a comparable total order of event labels | Labels alone do not tell a receiver whether an earlier unseen message can still arrive; no fault-tolerant agreement |
| Vector clock | Distinguishes causal precedence from concurrent events | More metadata as participants grow; concurrency still needs a business decision rule |
| Hybrid logical clock | Combines physical time with a logical component, useful for distributed database timestamps | A clock does not itself commit transactions, enforce shared seat capacity or elect a leader |
| Disruptor | Sequenced in-process publication with consumer dependency tracking | Performance engineering for a different runtime; no demonstrated need for a Java ring buffer here |
| Raft replicated state machine | Agrees on a committed log using leader election and replication | Requires nodes, quorum, recovery and deterministic replay; substantially more scope |
| Aeron Cluster | Implements Raft and sequences clients into a replicated log; documents order-book and RFQ use cases | A practical future option for high availability, not evidence that B3 uses it |
| Kafka partition log | Orders records within a partition and supports replicated event streams | No single total order across partitions; cross-mission shared capacity needs coordinated ownership |

Logical-clock comparisons follow [Lamport's original paper, sections on logical clocks and total ordering](https://lamport.azurewebsites.net/pubs/time-clocks.pdf). For vector clocks and their ability to identify concurrency, see [Fidge's original paper](https://ics.uci.edu/~cs230/reading/1.pdf); vector clocks are included as a conceptual alternative, not claimed as an exchange deployment.

HLC is a concrete distributed-database technique described by [Cockroach Labs](https://www.cockroachlabs.com/glossary/distributed-db/hybrid-logical-clock-hlc-timestamps/). Replica guarantees follow the [Raft paper](https://raft.github.io/raft.pdf) and [Aeron Cluster documentation](https://aeron.io/docs/aeron-cluster/overview/). Partition-level ordering and delivery limits follow [Apache Kafka's design documentation](https://kafka.apache.org/41/design/design/). These are distinct tools, not a chronological ladder in which the newest supersedes the others.

FIXP explicitly distinguishes recoverable, idempotent and unsequenced flows. Its delivery guarantees must not be confused with atomically committing a rescue mission effect. [FIXP 1.0, sections 3.4.4 and 3.5](https://www.fixtrading.org/wp-content/uploads/download-manager-files/FIX_Performance_Session_Layer_V1.0.pdf).

## Approaches considered for spec 007

1. **B3-style session sequencing and recovery, selected.** Give each ship session version separate directional counters, idempotent inbound responses with gap notification, and recoverable outbound decision reports. Keep business identity checks and atomic mission updates. The role mapping and in-memory scope are project adaptations.
2. **Central processing counter alone.** The earlier recommendation made local order inspectable but did not model per-session gaps or report retransmission, so it is not enough on its own. Its per-mission form returns as the decision-ordering layer above, alongside the session policy.
3. **Lamport timestamps or Raft.** Lamport metadata would still need a delivery/recovery policy. Raft would add replica agreement and availability requirements. Neither is established by the B3 public interface documents as its private engine mechanism, and neither is needed for this simulation.

The selected design follows the observable session guarantees rather than reproducing B3's private engine. Inbound response sequences and outbound report sequences are scoped independently; they do not create one global order across ships. Existing shared-capacity transactions remain necessary. Price-based matching is unrelated to choosing rescue ships by capacity and ETA.

## Decision ordering: how markets order competing actions

Session sequencing tells central which messages arrived. It does not say which of two competing actions on the same mission wins. Exchanges answer that question in the matching engine. This section records how they do it and which variant is closest to B3.

### What B3 does

- **Priority rule.** "B3 matches orders by price/time priority." The best price goes first; at the same price, "earlier bids and asks take precedence over later bids and asks" ([Binary EntryPoint 8.4.2.3, section 2.1](https://www.b3.com.br/data/files/69/35/F1/AB/94711A103BBB511AAC094EA8/BinaryEntryPoint-MessageSpecificationGuidelines-8.4.2.3-enUS.pdf)). B3's trading rules add that there is "no pro-rata matching for orders at the same price", except where its procedures manual says so, and that same-price orders follow "the chronological sequence of their registration" ([B3 trading characteristics and rules](https://www.b3.com.br/en_us/products-and-services/trading/equities/cash-equities/b3-trading-characteristics-and-rules.htm)).
- **Partitioning.** Order entry gateways read `marketSegmentID` "to redirect it to the correct matching engine" (section 4.6.3.1). Each segment has its own engine and its own order, so there is no single exchange-wide order.
- **FIFO intake.** The `LowPriority` flag means an order "has lost its priority in the FIFO queue to reach the matching engine" (section 4.6.3.1). Orders reach the engine first in, first out.
- **Engine-assigned identity.** The engine assigns `orderID` on entry and keeps it for the whole order life. `secondaryOrderID` changes on every client-initiated event (section 7.6.2).
- **Losing your place.** Changing price or increasing quantity loses priority; decreasing quantity keeps it (section 7.5). A replenished iceberg slice "enters in the open book with the least priority in the same price-level order list (same behavior as a new order)" (section 7.1.16).
- **Lineage.** A third-party overview describes PUMA's matching engine as based on CME Globex ([Trading Technologies B3 overview](https://library.tradingtechnologies.com/user-setup/b3-overview.html)). This is not a B3 statement; it is background only.
- **Observer order.** B3 market data carries a per-instrument report sequence (`RptSeq`) beside the per-channel packet sequence, so a receiver can detect a missing update for one book ([Binary UMDF guidelines 2.3.1.2](https://www.b3.com.br/data/files/84/B7/1D/9E/AB611A103BBB511AAC094EA8/BinaryUMDF-MessageSpecificationGuidelines-v.2.3.1.2-enUS.pdf)).

### Current solutions in use

| Solution | Where it is used | Fit for rescue decisions |
| --- | --- | --- |
| Price/time (FIFO) priority | B3, Nasdaq OUCH books, most cash-equity books | Closest to B3. Rescue responses have no price, so only arrival time applies |
| Pro-rata and FIFO/pro-rata hybrids | CME, for some interest-rate products | Rejected. B3 does not pro-rate same-price orders, and a partial confirmation already closes its request |
| Price-firm-time priority | B3 retail liquidity provider book (section 7.1.6) | Rejected. It ranks a firm's own orders first; there is no rescue counterpart |
| Frequent batch or periodic auctions | Cboe periodic auctions: Europe since 2015, US since 2022; US volume up 109% in 2025 by Cboe's own figures ([Cboe 2025 review](https://www.cboe.com/insights/posts/2025-u-s-equities-year-in-review)) | Rejected. Batching delays each decision until the auction ends; a seat response needs an answer when it arrives |
| Single-writer sequencer per partition | B3 engine per market segment; LMAX Disruptor; Aeron Cluster users such as Bitvavo | Adopted as the execution model, in memory, without replication |
| Raft-replicated sequencer | Aeron Cluster, which aggregates and sequences client streams into one replicated log ([Aeron Cluster](https://github.com/real-logic/aeron/blob/master/aeron-cluster/README.md), [Bitvavo case study](https://aeron.io/case-studies/bitvavo-scaling-crypto-exchange-aeron-cluster/)) | Future option if central must survive a crash. Out of scope |

The CME supported-algorithms page cited above could not be fetched on 2026-11-17, so this research does not claim which CME product uses which algorithm.

### Selected: per-mission FIFO sequencer

| B3 matching engine | Rescue central |
| --- | --- |
| Market segment routes to one engine | A mission routes to one decision queue |
| Order book for one instrument | One mission's requests and seats |
| FIFO intake to the engine | Central arrival order for the mission |
| Price/time priority | Time only: rescue responses have no price |
| `orderID` stable, `secondaryOrderID` per event | Message identity stable, delivery identity per attempt |
| Modified or replenished order goes to the back | Retried message goes to the back |
| `RptSeq` per instrument | Mission order number on every decision report |

Central assigns the mission order number on commit, in the same transaction as the decision. The current in-memory lock serialises all missions, which is stricter than the specification needs; only per-mission order is required, so a later per-mission lock stays compatible.

Not adopted: price-based ranking of ships (mobilisation ranks candidates by capacity and arrival estimate in spec 006), pro-rata, auctions and replication. B3's faster cancellation path, which bypasses the risk engine (section 7.2), is not copied: central registers a cancellation in arrival order like any other decision.

## Repository evidence and planning work

- `rescue/communication/models.py` currently contains both communication classes and payload validation.
- `RescueCentral.record_response` in `rescue/application/central.py` owns classification and mutation together. Its actual outcomes include `late`, which the old spec omitted.
- `MemoryTransactionStore.transact` in `rescue/adapters/memory.py` serialises staged state publication under one lock. It protects shared capacity across sessions; it does not supply session counters or recovery history today.
- Experiment baselines copy message/delivery indices; session counters and retained reports must be copied consistently too.
- The communication UML/ER omit current request correlation and RTT fields; their refresh belongs with implementation, not a claim that today's diagrams already match future code.

Planning must define session/envelope storage, default local-session compatibility, legacy baseline migration, report retention, public diagnostics, decision precedence and integration edits. It must cover inbound gaps that allow progress, delayed skipped messages, fresh-number retries, outbound replay, controls, recovery rejection, stale versions, rollback, deadline equality and copied-run continuation. See the [maintainability contract](contracts/maintainability.md) and [decision with worked examples](../../docs/architecture/communication-ordering.md).

## Planning decisions (Phase 0 of `/speckit-plan`, 2026-11-17)

Each decision below resolves an open point that the specification left to planning. Format: decision, rationale, alternatives considered.

### P1. The mission order number already exists

- **Decision**: Use `RequestHistoryEntry.mission_sequence` as the mission order number. `rescue/mission/rules/_accounting.py` assigns it as `len(mission.history) + 1` inside the transaction that appends the entry. Decision reports copy it.
- **Rationale**: It is already gapless, per mission, assigned on commit, carried by copied baselines, and absent after a failed transaction. That is exactly FR-012 and FR-013. A second counter would have to stay in step with this one.
- **Alternatives**: a separate per-mission counter in `RunState` (duplicates state); a run-wide counter (orders unrelated missions, which FR-012 forbids).
- **Consequence for the spec**: responses that append nothing to mission history get no number. Their report carries `after_mission_sequence`, the last number they were evaluated after. The spec's edge case and the decision document's worked example were corrected to say so.

### P2. Central arrival order is lock registration order

- **Decision**: "Central arrival order" means the order in which operations enter `MemoryTransactionStore.transact`. That is B3's "chronological sequence of their registration".
- **Rationale**: The single lock already serialises every operation, so one mission's decisions are registered one at a time. `threading.Lock` does not promise first-come acquisition among waiting threads, so the order is fixed at registration, not at the moment a thread starts waiting. The README states this.
- **Alternatives**: a FIFO ticket queue in front of the lock (adds a mechanism to order threads that arrive within microseconds; no test could tell them apart); a per-mission lock (allowed later, not needed now).

### P3. Default local session keeps old calls unchanged

- **Decision**: `RecordResponse` gains `envelope: SessionEnvelope | None = None`. With `None`, central uses the default session `local:<ship_id>` (or `local:unknown` when the request is unknown), version 1, and assigns the next expected inbound number itself. That number can never create a gap or a duplicate.
- **Rationale**: Every existing call, test and the demo give the same results (FR-011). Sequenced calls opt in.
- **Alternatives**: require envelopes everywhere (breaks every caller); skip sessions for unsequenced calls (two code paths for decision reports).

### P4. Sessions live in `RunState.session_index`

- **Decision**: `RunState`, `RunBaseline` and `RunSnapshot` gain `session_index: tuple[CommunicationSession, ...] = ()`. The experiments runner copies it where it copies `message_index` today (`rescue/experiments/runner.py`, baseline install and final snapshot).
- **Rationale**: The same immutable-tuple pattern as the other indices. Copies are values, so a copied run cannot change its source (FR-007).
- **Legacy baselines**: an old baseline has no `session_index`, so it defaults to `()`. Default sessions start at 1 on first use. Unsequenced calls never check gaps, so old message and delivery indices stay valid. Original session numbers are not reconstructed from timestamps.

### P5. Session versions are implicit

- **Decision**: No open-session call. The first envelope for a session starts it. A higher version starts a new version with both counters at 1 and no retained reports. The same version resumes. A lower version is rejected as `stale_session` and changes nothing.
- **Rationale**: This covers resume, new version and stale traffic (Story 2.5) without an extra API.

### P6. Precedence inside `classify_delivery`

The first matching row wins. Rows 1-2 and 4 onwards keep today's `record_response` order, so FR-003 holds; row 3 is the new session step.

| # | Condition | Session effect | Delivery record | Result |
| --- | --- | --- | --- | --- |
| 1 | Known delivery identity, identical | none | none | `ignored` |
| 2 | Known delivery identity, different content | none | none | `rejected identity_conflict` |
| 3a | Received, envelope version lower than active | none | none | `rejected stale_session` |
| 3b | Received, sequence below expected | none | `ignored duplicate_sequence` | `ignored duplicate_sequence` |
| 3c | Received, sequence above expected | gap recorded as `NotApplied`; expected = n + 1 | continue | continue |
| 3d | Received, sequence equal to expected | expected = n + 1 | continue | continue |
| 4 | Known message identity, different content | (step 3 applied) | `rejected identity_conflict` | `rejected identity_conflict` |
| 5 | Unknown request | (step 3 applied if received) | `lost` or `ignored unknown_request` | as today |
| 6 | Send before request submission | | `rejected invalid_input` | as today |
| 7 | No receipt | none: central never received it | `lost transport_loss` | as today |
| 8 | Closed request; late if expired and received at or after the deadline | | `late` or `ignored closed_request` | as today |
| 9 | Received at or after an open request's deadline | | `late deadline_expired`, request expires | as today |
| 10 | Mission rule rejects | | `rejected <reason>` | as today |
| 11 | Otherwise | | `applied response_applied` | `applied` |

A lost attempt (row 7) never reaches step 3, because central did not receive it. That keeps the "lost send cannot advance the expected number" edge case true.

### P7. Decision reports

- **Decision**: Central issues one `DecisionReport` for every received delivery it records (rows 4-6 and 8-11), with the next outbound number of that session. The report holds: the session envelope, message and delivery identities, mission identity, disposition, reason, `mission_sequence` (set when the decision appended history) and `after_mission_sequence`. Rows 1-3b issue no report.
- **Rationale**: It matches B3 sending one execution report per accepted or rejected order. A duplicate that changed nothing gets no report, so it consumes no outbound number.

### P8. Recovery and controls

- **Decision**: `recover_reports(RecoverReports(session_id, version, from_sequence, count))` returns the retained reports in order, followed by a `SequenceControl(next_sequence)` for the live stream. It runs in one read transaction and changes no mission or delivery state. Rejections:
  - `stale_session`: the version is not active.
  - `recovery_out_of_range`: `from_sequence` is below 1, or the range is not retained.
  - `recovery_limit`: `count` is below 1 or above 1000.
  - `recovery_in_progress`: another request for this session is outstanding.
- **Outstanding requests**: in this synchronous simulation, a request and its replay finish inside one transaction, so the application can never observe an outstanding request. The pure rule still models `outstanding_recovery` on the session, and its unit test covers the overlapping case. That is where the "one outstanding request" guarantee is enforced and proved.
- `synchronise_inbound(SynchroniseInbound(session_id, version, next_sequence))`: advancing records `NotApplied` for the skipped range; equal is a no-op; rewinding is rejected as `sequence_rewind`. Controls never consume business numbers.
- **Ship side**: a pure `ReportCursor` with a `receive_report` rule. It accepts the expected report, buffers later ones, flags the gap to request, and drains the buffer in order after recovery. Tests use it; the experiments runner does not need it.

### P9. Closed vocabularies

- `DeliveryDisposition`: `applied`, `ignored`, `lost`, `rejected`, `late`.
- `DeliveryReason`: every value `record_response` writes today. That is `response_applied`, `identity_conflict`, `transport_loss`, `unknown_request`, `invalid_input`, `closed_request` and `deadline_expired`, plus each mission-rule reason `_reason` can return: `unknown_mission`, `unknown_ship`, `insufficient_demand`, `insufficient_capacity`, `unavailable`, `expired_quote` and `revision_conflict`. New: `duplicate_sequence`.
- `FlowDirection`: `inbound`, `outbound`.
- `RecoveryRejection`: `stale_session`, `recovery_out_of_range`, `recovery_limit`, `recovery_in_progress`, `sequence_rewind`.
- `ErrorReason` in `rescue/application/contracts.py` gains `duplicate_sequence`, `stale_session`, `sequence_rewind`, `recovery_out_of_range`, `recovery_limit`, `recovery_in_progress` and `unknown_session`, because `Result` validates reasons.
- All are `StrEnum`, so stored and rendered text stays the same, as in spec 004.

### P10. Layering

- **Decision**: `rescue/communication/` follows the spec 004 shape. `models/` holds values and vocabularies; `rules/` holds pure functions; `rules` imports `models`, never the reverse. The application gathers facts as primitives (request open, deadline, submitted time), so communication never imports mission. New import-linter contracts: `communication-isolated` and `communication-layers`. The communication coverage line in the Makefile gains `--fail-under=100`.
- **Rationale**: Under cosmic-python, pure rules and values are the models layer, and `rules/` is a peer of `models/` as in 004. Clean Architecture: policy (classification, sequencing) has no knowledge of the store, the lock or mission internals, and the application is the only place that composes them. FR-010 forbids importing anything but `rescue.values` and the standard library.
- **Alternatives**: one `services/` folder inside communication (would mix orchestration into the domain); passing `Mission` into classification (couples communication to mission and breaks FR-010).

### P11. Application surface stays in `RescueCentral`

- **Decision**: `record_response` becomes thin: it gathers facts, calls `classify_delivery`, `accept_inbound` and `issue_report`, and publishes everything in one transaction. New methods: `recover_reports`, `synchronise_inbound` and `get_session`. All stay on `RescueCentral`.
- **Rationale**: Spec 008 splits `central.py` into one service per use case, and the roadmap requires 007 to merge first. Adding a new application module now would be moved again by 008.
- **Alternatives**: `rescue/application/communication/` now (pre-empts 008's layout decision).

### P12. Parallel delivery without commits

- **Decision**: Tasks marked `[P]` in one wave are dispatched as parallel subagents in the same checkout. Each owns a disjoint file list. Nobody commits (AGENTS.md section 8), and the controller runs `make check-all` at the end of each wave. Review packages are `git diff` of the owned paths plus their new files.
- **Rationale**: The constitution allows parallel writers with non-overlapping ownership. superpowers:subagent-driven-development warns against parallel implementers because they collide in shared files and in commits. Disjoint ownership removes the first risk, and no commits removes the second. This is a recorded deviation, approved by the maintainer's request for `[P]` dispatch.
- **Alternatives**: strictly serial dispatch (about 30 tasks, roughly three times the wall-clock time); one worktree per `[P]` task (needs commits to merge back, which AGENTS.md forbids without the maintainer's request).
