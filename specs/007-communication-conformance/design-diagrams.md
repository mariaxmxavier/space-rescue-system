# Design Diagrams: 007 Communication Conformance

**Change**: 007-communication-conformance | **Design**: [plan.md](plan.md), [data-model.md](data-model.md), [research.md](research.md) (P1-P12)

## Color Conventions

| Flow Type | Color | Hex |
|-----------|-------|-----|
| Submission / happy-path | blue | `#2196F3` |
| Validation / processing | amber | `#FF9800` |
| Safety / blocking / rejection | red | `#F44336` |
| Routing / delivery / success | green | `#4CAF50` |
| Error / failure | crimson | `#B71C1C` |

## 1. Component Dependencies

Imports point inwards: `application.central` → `communication.rules` → `communication.models` → `rescue.values`. Communication never imports mission; central converts mission facts to `DeliveryFacts` primitives and reads `mission_sequence` as an `int`.

```mermaid
flowchart TD
    subgraph ext["Out of Scope (callers)"]
        SHIP(["Ship / experiments runner"])
        OP(["Operator / demo"])
    end

    subgraph app["rescue.application (services)"]
        RC[["RescueCentral"]]
        STORE["TransactionStore port"]
    end

    subgraph adapters["rescue.adapters"]
        MEM["MemoryTransactionStore (one lock)"]
    end

    subgraph rules["rescue.communication.rules"]
        CLS["classify_delivery"]
        ACC["accept_inbound"]
        ISS["issue_report"]
        REC["recover_reports"]
        SYN["synchronise_inbound"]
        RCV["receive_report"]
    end

    subgraph models["rescue.communication.models"]
        MSG(["CommunicationMessage"])
        DEL(["MessageDelivery"])
        FACTS(["DeliveryFacts / DeliveryDecision"])
        ENV(["SessionEnvelope"])
        SES(["CommunicationSession"])
        GAP(["NotApplied"])
        REP(["DecisionReport"])
        CUR(["ReportCursor"])
    end

    subgraph mission["rescue.mission (unchanged)"]
        HIST(["RequestHistoryEntry.mission_sequence"])
    end

    SHIP -.->|"1. record_response(envelope)"| RC
    OP -.->|"cancel / expire"| RC
    RC -->|"2. transact"| STORE
    MEM -->|"implements"| STORE
    RC -->|"3. classify"| CLS
    RC -->|"4. sequence"| ACC
    RC -->|"5. apply_outcome"| HIST
    RC -->|"6. report"| ISS
    RC -->|"recover"| REC
    RC -->|"synchronise"| SYN
    SHIP -.->|"cursor"| RCV
    CLS -.->|"_uses_"| FACTS
    ACC -.->|"_updates_"| SES
    ACC -.->|"_produces_"| GAP
    ISS -.->|"_builds_"| REP
    REC -.->|"_reads_"| REP
    RCV -.->|"_updates_"| CUR
    DEL -.->|"_carries_"| ENV
    REP -.->|"_copies_ int"| HIST

    style SHIP stroke-dasharray:5 5,stroke:#999,fill:#f5f5f5,color:#333
    style OP stroke-dasharray:5 5,stroke:#999,fill:#f5f5f5,color:#333
    style RC fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#333
    style STORE fill:#FFF3E0,stroke:#EF6C00,color:#333
    style MEM fill:#FFF3E0,stroke:#EF6C00,color:#333
    style CLS fill:#FFF3E0,stroke:#EF6C00,color:#333
    style ACC fill:#FFF3E0,stroke:#EF6C00,color:#333
    style ISS fill:#FFF3E0,stroke:#EF6C00,color:#333
    style REC fill:#FFF3E0,stroke:#EF6C00,color:#333
    style SYN fill:#FFF3E0,stroke:#EF6C00,color:#333
    style RCV fill:#FFF3E0,stroke:#EF6C00,color:#333
    style MSG fill:#E8EAF6,stroke:#7986CB,color:#333
    style DEL fill:#E8EAF6,stroke:#7986CB,color:#333
    style FACTS fill:#E8EAF6,stroke:#7986CB,color:#333
    style ENV fill:#E8EAF6,stroke:#7986CB,color:#333
    style SES fill:#E8EAF6,stroke:#7986CB,color:#333
    style GAP fill:#E8EAF6,stroke:#7986CB,color:#333
    style REP fill:#E8EAF6,stroke:#7986CB,color:#333
    style CUR fill:#E8EAF6,stroke:#7986CB,color:#333
    style HIST fill:#E8EAF6,stroke:#7986CB,color:#333

    linkStyle 0 stroke:#2196F3,stroke-width:2px
    linkStyle 1 stroke:#2196F3,stroke-width:2px
    linkStyle 2 stroke:#FF9800,stroke-width:2px
    linkStyle 4 stroke:#FF9800,stroke-width:2px
    linkStyle 5 stroke:#FF9800,stroke-width:2px
    linkStyle 6 stroke:#4CAF50,stroke-width:2px
    linkStyle 7 stroke:#4CAF50,stroke-width:2px
```

---

## 2. Sequence Diagram

One `record_response` transaction (research P6, P7), a gap, a race lost to a cancellation, and report recovery.

```mermaid
sequenceDiagram
    participant S as Ship session S1 v1
    participant RC as RescueCentral
    participant ST as MemoryTransactionStore
    participant CR as communication.rules
    participant MR as mission.rules

    rect rgb(33,150,243)
        Note over S,MR: Happy path: inbound 1 == expected 1
        S ->> RC: record_response(M1/D1, seq 1)
        RC ->> ST: transact(operation)
        ST ->> CR: classify_delivery(facts) → apply
        ST ->> CR: accept_inbound(session, env 1) → expected 2
        ST ->> MR: apply_outcome → history entry, mission_sequence 3
        ST ->> CR: issue_report(session, decision, 3) → report out 1
        ST -->> RC: publish session + delivery + mission + report together
        RC -->> S: applied
    end

    rect rgb(255,152,0)
        Note over S,MR: Gap: inbound 3 while expecting 2
        S ->> RC: record_response(M2/D3, seq 3)
        RC ->> ST: transact(operation)
        ST ->> CR: accept_inbound → NotApplied(2, 1), expected 4
        ST ->> MR: business rules for M2 run now, no waiting
        RC -->> S: business result of M2 (gap kept in session)
    end

    rect rgb(244,67,54)
        Note over S,MR: Race: cancellation registered first
        RC ->> ST: cancel_request(R1) → mission_sequence 4
        S ->> RC: record_response(R1 confirm, seq 4)
        ST ->> CR: classify_delivery → ignored closed_request
        ST ->> CR: issue_report(mission_sequence None, after 4)
        RC -->> S: ignored closed_request
    end

    rect rgb(76,175,80)
        Note over S,MR: Recovery of report 1
        S ->> RC: recover_reports(v1, from 1, count 1)
        RC ->> ST: transact(read only)
        ST ->> CR: recover_reports(session, request)
        RC -->> S: original report 1, then SequenceControl(next 4)
    end

    rect rgb(183,28,28)
        Note over S,MR: Error: stale version or bad range
        S ->> RC: record_response(seq 1, version 0)
        RC -->> S: rejected stale_session, nothing published
        S ->> RC: recover_reports(count 1001)
        RC -->> S: rejected recovery_limit
    end
```

---

## 3. State Machines

### 3.1 CommunicationSession (inbound expectation)

```mermaid
flowchart TD
    NEW([No session]) -->|"first envelope v"| ACTIVE[Active v, expected n]
    ACTIVE -->|"seq == n: expected n+1"| ACTIVE
    ACTIVE -->|"seq > n: NotApplied(n, seq-n), expected seq+1"| ACTIVE
    ACTIVE -->|"seq < n: duplicate_sequence"| ACTIVE
    ACTIVE -->|"synchronise advance: NotApplied"| ACTIVE
    ACTIVE -->|"synchronise rewind"| REWIND([rejected sequence_rewind])
    ACTIVE -->|"higher version: counters 1, reports cleared"| ACTIVE
    ACTIVE -->|"lower version"| STALE([rejected stale_session])

    style NEW fill:#2196F3,color:#fff
    style ACTIVE fill:#FF9800,color:#fff
    style REWIND fill:#F44336,color:#fff
    style STALE fill:#F44336,color:#fff
```

### 3.2 Report recovery (one session)

```mermaid
flowchart TD
    IDLE([No outstanding request]) -->|"request in range, count 1..1000"| OUT[Outstanding]
    OUT -->|"replay originals + SequenceControl"| DONE([Completed])
    OUT -->|"second request"| BUSY([rejected recovery_in_progress])
    IDLE -->|"count outside 1..1000"| LIMIT([rejected recovery_limit])
    IDLE -->|"range not retained"| RANGE([rejected recovery_out_of_range])
    IDLE -->|"inactive version"| STALE([rejected stale_session])

    style IDLE fill:#2196F3,color:#fff
    style OUT fill:#FF9800,color:#fff
    style DONE fill:#4CAF50,color:#fff
    style BUSY fill:#F44336,color:#fff
    style LIMIT fill:#F44336,color:#fff
    style RANGE fill:#F44336,color:#fff
    style STALE fill:#F44336,color:#fff
```

### 3.3 ReportCursor (ship side)

```mermaid
flowchart TD
    WAIT([Expect k]) -->|"report k: deliver, drain buffer"| WAIT
    WAIT -->|"report > k: buffer, gap k..report-1"| GAPPED[Gap pending]
    GAPPED -->|"recovered k..: deliver in order, drain buffer"| WAIT
    WAIT -->|"report < k: no effect"| WAIT

    style WAIT fill:#2196F3,color:#fff
    style GAPPED fill:#FF9800,color:#fff
```
