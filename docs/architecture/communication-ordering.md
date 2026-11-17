# Communication ordering: B3-style session sequencing and decision ordering

**Decision date**: 2026-11-17. **Selected by**: maintainer. **Implementation status**: implemented on branch 007-communication-conformance; specified in [feature 007](../../specs/007-communication-conformance/spec.md).

## Why communication exists

Ship responses can be lost, repeated or delayed. Communication identifies what arrived and what is missing. Mission rules decide whether seats can change. Session recovery must never apply the same confirmation twice.

Before 007, message data lived in `rescue/communication/models.py`, and `RescueCentral.record_response` combined classification and application changes. The memory adapter serialises transactions under one lock. Feature 007 separates those responsibilities and introduces explicit sessions and recovery.

## Decision

Use two published B3 layers, adapted to the rescue simulation: the Binary EntryPoint session pattern for delivery, and the matching engine's per-segment FIFO ordering for competing decisions (see [Decision ordering](#decision-ordering-per-mission-fifo-sequencer)). The session pattern:

- Ship-to-central responses use an **idempotent inbound flow**.
- Central-to-ship decision reports use a **recoverable outbound flow**.
- Each logical session version has independent counters for its two directions.
- Missing inbound numbers produce a `NotApplied` notification; later valid messages can proceed.
- Missing outbound reports can be requested and replayed with their original numbers.

This follows the documented session behavior, not an inferred B3 internal matching-engine algorithm. [B3 Binary EntryPoint 8.4.2.3, sections 4.5.4-4.6.3](https://www.b3.com.br/data/files/69/35/F1/AB/94711A103BBB511AAC094EA8/BinaryEntryPoint-MessageSpecificationGuidelines-8.4.2.3-enUS.pdf).

| Approach | What it provides | Decision |
| --- | --- | --- |
| B3-style session sequencing and recovery | Per-direction identities, gap handling and report recovery | Selected as the closest published B3 communication policy |
| Central processing counter alone | Local audit order, without session gap detection or recovery | Insufficient alone; kept per mission as the decision order |
| Price/time priority per mission (B3 matching engine) | One authoritative order of competing decisions per mission | Selected for decision ordering, time half only |
| Pro-rata or periodic auctions | Proportional or batched allocation | Rejected; see research |
| Lamport clocks | Comparable causal labels across processes | Does not supply the required recovery behavior |
| Raft replicated log | Replica agreement and failover | Outside the current in-memory scope |

The earlier central-counter-only proposal is superseded. The central transaction store remains responsible for shared seat safety.

## Mapping to this project

A session belongs to one ship and one rescue run. Its identity, version and direction scope its sequence numbers. Version and sequence are envelope metadata, separate from immutable message content and delivery-attempt identity.

Central takes B3's receiver role for ship responses; a decision report is the rescue analogue of an execution report. This mapping is a project decision. It is not a B3-certified implementation and adds no exchange connection, binary encoding or sockets.

Each direction starts at 1 for a new explicit session version. Resuming an existing version keeps its counters and report history. Delayed traffic from an old version cannot update the active one. Independent runs have independent sessions; copied baselines carry counters and history without modifying their source.

## Inbound algorithm

Let `expected` be the next inbound number central expects, and `n` the number carried by a received business envelope.

| Condition | Session action | Business action |
| --- | --- | --- |
| `n < expected` | Treat as already consumed or skipped | Do not execute again; preserve existing identity-conflict checks |
| `n == expected` | Stage `expected = n + 1` | Apply normal message, request and deadline rules once |
| `n > expected` | Notify missing range `[expected, n - 1]`; stage `expected = n + 1` | Consider this message now; do not wait for the missing range |

The receiver progress, delivery decision, mission transition and any new outbound report commit in one transaction. A well-formed received business message can consume its number even if the mission rejects it. If the transaction fails, none of those receiver changes publish.

A sender consumes a number when sending, including a send that is lost. Recording simulated loss at central does not mean it received the business envelope and must not advance its inbound expectation. The next received envelope exposes any gap.

Recovery of a skipped inbound response uses a fresh sequence and delivery identity, while retaining its immutable message identity. Sequence checks alone are insufficient: that same business message may already have succeeded through another attempt, so identity and closed-request rules still apply.

## Outbound recovery and controls

Central assigns its own outbound sequence to each new decision report and retains that report within the active session version. The ship tracks its next expected report. On a gap it requests the missing retained range, buffers later reports, and applies reports in order after recovery. Repeated reports have no additional application effect.

Replay preserves report identity, number and content. It does not rerun `record_response`, allocate another business number or change seats. Recovery is limited to the active version and retained history. Missing or invalid ranges produce an explicit recovery rejection; they do not manufacture reports.

Model at most one outstanding recovery request per session, with at most 1000 reports per request, following the bounded recovery pattern. Controls such as `NotApplied`, `Sequence` and recovery boundaries do not consume business sequence numbers. `Sequence(nextSeqNo)` synchronises the expected position; advancing an inbound expectation reports the skipped range, and rewinding the active flow is rejected. At recovery completion a `Sequence` control identifies the live stream's next number.

The simulation exercises these controls through explicit calls. Real heartbeat timers, authentication, negotiation wire formats, daily trading schedules and transport connections are outside 007.

## Worked example: missing ship response

Session `S1`, version `V1`, starts with central expecting inbound 1. Request `R1` has 10 pending seats; request `R2` has 4 pending seats. Both deadlines are later than the example's receipt times.

| Step | Inbound envelope | Result | Next inbound expected |
| --- | --- | --- | --- |
| 1 | `M1 / D1`, sequence 1: partial acceptance of 6 for R1, lost | No receipt; R1 still pending | 1 |
| 2 | `M2 / D2`, sequence 2: refusal for R2, received | Emit `NotApplied(1, count=1)` and process refusal; R2 closes | 3 |
| 3 | `M1 / D3`, sequence 3: retry of M1, received | Apply 6 seats once; R1 closes and releases the other 4 | 4 |
| 4 | Delayed original sequence 1 | Already skipped; do not apply again | 4 |
| 5 | `M1 / D4`, sequence 4: same immutable message again | Consume envelope number but ignore closed request; confirmed seats stay 6 | 5 |

The gap notification is separate from the business result: sequence 2 can be successfully processed while sequence 1 remains unreceived. A sender can recover with a fresh number or choose not to retry.

## Worked example: missing central report

Central generates report 1 for the R2 refusal and report 2 for the R1 partial acceptance. Report 1 is lost; the ship receives report 2 while expecting 1.

1. The ship buffers report 2 and requests report 1 from the active version.
2. Central returns the original report 1 with outbound sequence 1.
3. The ship consumes report 1, then buffered report 2, and next expects 3.
4. Central signals the live stream position. No seats change during report replay.

Inbound and outbound sequence numbers are independent: inbound 2 produced outbound report 1 in this example. They are not a single run-wide counter.

## Decision ordering: per-mission FIFO sequencer

Sessions tell central what arrived. Decision ordering tells everyone which competing action took effect first. This follows B3's matching-engine layer: each market segment has one engine, orders reach it first in, first out, and the book ranks them by price/time priority ([B3 Binary EntryPoint 8.4.2.3, sections 2.1, 4.6.3.1 and 7.5](https://www.b3.com.br/data/files/69/35/F1/AB/94711A103BBB511AAC094EA8/BinaryEntryPoint-MessageSpecificationGuidelines-8.4.2.3-enUS.pdf)).

In the rescue system a mission plays the market segment and its order book. Rescue responses carry no price, so only the time half of the rule applies:

1. Central registers decisions for one mission one at a time, in the order they arrive at central.
2. Each committed decision that changes the mission history gets the next **mission order number**, starting at 1, with no gaps or reuse. This is the existing `RequestHistoryEntry.mission_sequence`; 007 exposes it, it does not add a second counter.
3. Sender time, session sequence and attempt number never move a decision in that order.
4. A retried message enters at the back, keeping its message identity, as a modified B3 order loses its place.
5. Failed transactions, report replays and duplicates without effect consume no number.
6. Every decision report carries its mission order number beside its session sequence, like B3's per-instrument `RptSeq`, so an observer can rebuild one mission's history across ship sessions.

Different missions are ordered independently. Pro-rata, auctions, price-based ship ranking and replication are not adopted; the [research](../../specs/007-communication-conformance/research.md) explains why.

### Worked example: cancellation races a confirmation

Mission `A` needs 10 seats. Request `R1` asks ship S1 for 6; request `R2` asks ship S2 for 4. Sending them committed mission order numbers 1 and 2.

| Central arrival | Action | Mission order | Result |
| --- | --- | --- | --- |
| 1st | S2 confirms 4 for R2 (session S2, inbound 1) | 3 | R2 closes; 4 seats confirmed |
| 2nd | Operator cancels R1 | 4 | R1 closes as cancelled; 6 seats released |
| 3rd | S1 confirms 6 for R1 (session S1, inbound 1), sent before the cancellation | none; evaluated after 4 | Closed-request outcome; seats stay 4 |
| 4th | Exact duplicate of the S2 confirmation | none | Ignored without history |

S1 sent its confirmation before the operator acted, but central registered the cancellation first, so the cancellation wins. Both ships' session numbers are 1; only the mission order says which decision came first. The rejected confirmation changes no history, so it takes no number; its report says it was evaluated after mission order 4.

## Guarantees and limits

- Equal sender timestamps are harmless to sequence checks. A receipt at or after the response deadline is late: it expires an open request or is recorded late against an expired one. A request already closed by another outcome still reports `closed_request`.
- Per-session sequencing does not globally order two ships. The mission order number does, within one mission. The central transaction lock and mission invariants protect shared capacity across sessions.
- Receiving sequence 3 does not prove sequence 2 was received; the missing range remains explicit.
- Gap notification, transport acceptance and business success are different results.
- In-memory replay works only while the relevant state exists. Disk durability, replica failover and whole-system event replay are outside 007.
- Existing unsequenced calls keep a default local-session path. Envelope assignment and legacy baseline migration never reconstruct sender order from timestamps.

## Code and model trace

| Part | Responsibility |
| --- | --- |
| Communication models and pure rules: `rescue/communication/models/`, `rescue/communication/rules/` (`classify_delivery.py`, `accept_inbound.py`, `synchronise_inbound.py`, `issue_report.py`, `receive_report.py`, `recover_reports.py`) | Session envelopes, counters, gap decisions, immutable reports and classification |
| Mission order numbering: `rescue/mission/rules/_accounting.py`, `rescue/mission/models/mission/request_history_entry.py` | Assigns the next mission order number to each committed history row; decision reports carry it and never allocate one |
| Application response/recovery use cases: `rescue/application/central.py` (`RescueCentral.record_response`, `synchronise_inbound`, `recover_reports`, `get_session`, `get_deliveries`) | Gather facts, apply rules, stage mission and session changes, publish and replay reports |
| Simulated responses: `rescue/experiments/runner.py` | Schedules simulated ship responses and calls `record_response` on the default local session |
| Memory transaction adapter: `rescue/adapters/memory.py` | Atomically publish sequence state and mission state under one lock |
| Tests: `tests/unit/communication/`, `tests/integration/application/communication/`, `tests/integration/application/concurrency/`, `tests/integration/experiments/session_copy/`, `tests/architecture/communication_layout/`, `tests/architecture/boundaries/test_architecture.py` | Rule and model checks, delivery outcomes, sessions and recovery, mission order, concurrent and copied-run fixtures, layout, docstring and import checks |
| Communication UML | Message, delivery, session, control and report responsibilities |
| Communication ER | Stored session versions, directional sequences, report history and relationships |

- [Communication UML source](diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd)
- [Communication ER source](diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd)
- [Structure and docstring contract](../../specs/007-communication-conformance/contracts/maintainability.md)
- [Research and alternatives](../../specs/007-communication-conformance/research.md)
