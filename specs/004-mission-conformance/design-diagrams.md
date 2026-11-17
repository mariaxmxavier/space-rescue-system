# Design Diagrams: 004 Mission Conformance

**Change**: 004-mission-conformance | **Design**: [plan.md](plan.md), [data-model.md](data-model.md)

## Color Conventions

| Flow Type | Color | Hex |
|-----------|-------|-----|
| Submission / happy-path | blue | `#2196F3` |
| Validation / processing | amber | `#FF9800` |
| Safety / blocking / rejection | red | `#F44336` |
| Routing / delivery / success | green | `#4CAF50` |
| Error / failure | crimson | `#B71C1C` |

## 1. Component Dependencies

Imports point inwards: callers → `rules` → `models` → `rescue.values`. Callers use only the two
package `__init__`s (contracts/public-imports.md).

```mermaid
flowchart TD
    subgraph ext["Out of Scope (callers)"]
        APP(["application.central"])
        EXP(["experiments"])
        MOB(["mobilisation.policies"])
        MKT(["market.rules"])
        DEMO(["demo"])
    end

    subgraph rules["rescue.mission.rules"]
        REG["register"]
        ADD["add_request"]
        OUT["apply_outcome"]
        PRO["progress"]
        TIM["timing"]
        ACC["_accounting"]
    end

    subgraph models["rescue.mission.models"]
        subgraph agg["mission/ (aggregate)"]
            MIS(["Mission"])
            MD(["MissionData"])
            SR(["SeatRequest"])
            RHE(["RequestHistoryEntry"])
        end
        subgraph proj["projections/"]
            MP(["MissionProgress"])
            RT(["RequestTiming"])
        end
        VOC(["vocabulary"])
        VAL["_validation"]
    end

    VALUES(["rescue.values"])

    APP -.->|"1. register / add / apply"| REG
    APP -.-> ADD
    APP -.-> OUT
    EXP -.->|"read"| PRO
    MOB -.->|"read"| PRO
    DEMO -.-> REG
    MKT -.->|"_reads outcome_"| SR

    REG -.->|"_builds_"| MIS
    ADD -->|"2. checks"| ACC
    OUT -->|"3. checks"| ACC
    ACC -.->|"_appends_"| RHE
    OUT -.->|"_replaces_"| SR
    PRO -.->|"_produces_"| MP
    TIM -.->|"_produces_"| RT

    MIS -.-> SR
    MIS -.-> RHE
    SR -.-> VOC
    RHE -.-> VOC
    MP -.-> VOC
    SR --> VAL
    VAL --> VALUES

    style APP stroke-dasharray:5 5,stroke:#999,fill:#f5f5f5,color:#333
    style EXP stroke-dasharray:5 5,stroke:#999,fill:#f5f5f5,color:#333
    style MOB stroke-dasharray:5 5,stroke:#999,fill:#f5f5f5,color:#333
    style MKT stroke-dasharray:5 5,stroke:#999,fill:#f5f5f5,color:#333
    style DEMO stroke-dasharray:5 5,stroke:#999,fill:#f5f5f5,color:#333
    style REG fill:#FFF3E0,stroke:#EF6C00,color:#333
    style ADD fill:#FFF3E0,stroke:#EF6C00,color:#333
    style OUT fill:#FFF3E0,stroke:#EF6C00,color:#333
    style PRO fill:#FFF3E0,stroke:#EF6C00,color:#333
    style TIM fill:#FFF3E0,stroke:#EF6C00,color:#333
    style ACC fill:#FFF3E0,stroke:#EF6C00,color:#333
    style VAL fill:#FFF3E0,stroke:#EF6C00,color:#333
    style MIS fill:#E8EAF6,stroke:#7986CB,color:#333
    style MD fill:#E8EAF6,stroke:#7986CB,color:#333
    style SR fill:#E8EAF6,stroke:#7986CB,color:#333
    style RHE fill:#E8EAF6,stroke:#7986CB,color:#333
    style MP fill:#E8EAF6,stroke:#7986CB,color:#333
    style RT fill:#E8EAF6,stroke:#7986CB,color:#333
    style VOC fill:#E8EAF6,stroke:#7986CB,color:#333
    style VALUES fill:#E8EAF6,stroke:#7986CB,color:#333

    linkStyle 0 stroke:#2196F3,stroke-width:2px
    linkStyle 8 stroke:#FF9800,stroke-width:2px
    linkStyle 9 stroke:#FF9800,stroke-width:2px
```

## 2. Sequence Diagram

`apply_outcome` on a pending request (happy path) and on a closed request (rejection).

```mermaid
sequenceDiagram
    participant RC as RescueCentral
    participant AO as apply_outcome
    participant ACC as _accounting
    participant M as Mission

    rect rgb(33,150,243)
        Note over RC,M: Happy path: pending → partially_accepted
        RC ->> AO: apply_outcome(mission, request_id, PARTIALLY_ACCEPTED, 2, context)
        AO ->> AO: check outcome ∈ RequestOutcome.final(), 0 < 2 < requested, before deadline
        AO ->> ACC: append_history(action=PARTIALLY_ACCEPTED, +2 C, −requested P)
        AO ->> ACC: account(updated) → C + P ≤ D
        AO -->> RC: new Mission (request closed, remainder released)
    end

    rect rgb(183,28,28)
        Note over RC,M: Rejection: request already closed
        RC ->> AO: apply_outcome(mission, request_id, REFUSED, 0, context)
        AO -->> RC: DomainValidationError("closed requests cannot change outcome")
        Note over RC,M: original Mission unchanged (Constitution III)
    end
```

## 3. State Machines

### 3.1 SeatRequest

```mermaid
flowchart TD
    START([add_request]) --> PENDING[pending]
    PENDING -->|"ship confirms all"| ACC([accepted])
    PENDING -->|"ship confirms 0 < c < N"| PART([partially_accepted])
    PENDING -->|"ship refuses"| REF([refused])
    PENDING -->|"central cancels"| CAN([cancelled])
    PENDING -->|"deadline passes"| EXP([expired])

    style START fill:#2196F3,color:#fff
    style PENDING fill:#FF9800,color:#fff
    style ACC fill:#4CAF50,color:#fff
    style PART fill:#4CAF50,color:#fff
    style REF fill:#B71C1C,color:#fff
    style CAN fill:#B71C1C,color:#fff
    style EXP fill:#B71C1C,color:#fff
```

### 3.2 MissionProgress status (derived, not stored)

```mermaid
flowchart TD
    NEED[needs_more_help<br/>C + P < D] -->|"add_request fills gap"| WAIT[awaiting_responses<br/>C + P = D]
    WAIT -->|"refused / cancelled / expired / partial"| NEED
    WAIT -->|"all pending accepted"| DONE([complete<br/>C = D])
    NEED -->|"accept closes gap"| DONE

    style NEED fill:#F44336,color:#fff
    style WAIT fill:#FF9800,color:#fff
    style DONE fill:#4CAF50,color:#fff
```
