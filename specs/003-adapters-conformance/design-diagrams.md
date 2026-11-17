# Design Diagrams: 003-adapters-conformance

**Change**: 003-adapters-conformance | **Design**: [plan.md](plan.md), [data-model.md](data-model.md)

Colors: blue = happy path / wiring, amber = processing, red = blocked import, crimson = error,
green = success. Bold blue nodes are runtime components; orange nodes are ports and adapters;
indigo rounded nodes are domain records.

## 1. Component Dependencies

```mermaid
flowchart TD
    subgraph root["Composition root"]
        BOOT[["bootstrap.new_run"]]
    end

    subgraph application["application (services)"]
        RC[["RescueCentral"]]
        RUN[["experiments.runner"]]
    end

    subgraph ports["adapters/ports (ABCs)"]
        TS["TransactionStore"]
        CK["Clock"]
        IDS["IdSource"]
    end

    subgraph memory["adapters/memory"]
        MTS["MemoryTransactionStore"]
        ZC["ZeroClock"]
        SIS["SequenceIdSource"]
    end

    subgraph domain["domain records"]
        RS(["RunState"])
    end

    BOOT -->|"1. builds"| MTS
    BOOT -->|"2. builds"| ZC
    BOOT -->|"3. builds"| SIS
    BOOT ==>|"4. injects ports"| RC
    RC -->|"5. transact / snapshot"| TS
    RC -.->|"holds, no call yet"| CK
    RC -->|"next_id"| IDS
    RUN -->|"snapshot"| TS
    MTS -.->|"_implements_"| TS
    ZC -.->|"_implements_"| CK
    SIS -.->|"_implements_"| IDS
    MTS -.->|"_holds_"| RS
    TS -.->|"_uses_"| RS

    style BOOT fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#333
    style RC fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#333
    style RUN fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#333
    style TS fill:#FFF3E0,stroke:#EF6C00,color:#333
    style CK fill:#FFF3E0,stroke:#EF6C00,color:#333
    style IDS fill:#FFF3E0,stroke:#EF6C00,color:#333
    style MTS fill:#FFF3E0,stroke:#EF6C00,color:#333
    style ZC fill:#FFF3E0,stroke:#EF6C00,color:#333
    style SIS fill:#FFF3E0,stroke:#EF6C00,color:#333
    style RS fill:#E8EAF6,stroke:#7986CB,color:#333

    linkStyle 0,1,2,3 stroke:#2196F3,stroke-width:2px
    linkStyle 4,5,6,7 stroke:#FF9800,stroke-width:2px
```

Import contracts guarding these edges (red = forbidden):

```mermaid
flowchart LR
    APP["application / experiments / demo"] -->|"forbidden"| MEM["adapters.memory"]
    ADP["adapters"] -->|"forbidden"| OUT["bootstrap, demo, experiments, application.central, domain packages"]
    ADP -->|"allowed (FR-010, until 008)"| ST(["application.state"])
    BOOT2[["bootstrap"]] -->|"allowed"| MEM

    style APP fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#333
    style BOOT2 fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#333
    style MEM fill:#FFF3E0,stroke:#EF6C00,color:#333
    style ADP fill:#FFF3E0,stroke:#EF6C00,color:#333
    style OUT fill:#FFEBEE,stroke:#F44336,color:#333
    style ST fill:#E8EAF6,stroke:#7986CB,color:#333

    linkStyle 0,1 stroke:#F44336,stroke-width:2px
    linkStyle 2,3 stroke:#4CAF50,stroke-width:2px
```

## 2. Sequence Diagram

```mermaid
sequenceDiagram
    participant C as Caller
    participant B as bootstrap.new_run
    participant RC as RescueCentral
    participant TS as MemoryTransactionStore
    participant ID as SequenceIdSource

    rect rgb(33,150,243)
        Note over C,ID: Wiring
        C ->> B: new_run(run_id, central_id)
        B ->> TS: MemoryTransactionStore(RunState)
        B ->> RC: RescueCentral(store, clock, id_source)
        B -->> C: RunContext
    end

    rect rgb(76,175,80)
        Note over C,ID: Happy path
        C ->> RC: use case
        RC ->> ID: next_id(kind)
        ID -->> RC: KIND-00000001
        RC ->> TS: transact(op)
        TS ->> TS: lock, op(state) -> (state', result), publish state'
        TS -->> RC: result
        RC -->> C: Result
    end

    rect rgb(183,28,28)
        Note over C,ID: Error path
        C ->> RC: invalid use case
        RC ->> TS: transact(op)
        TS ->> TS: op raises, nothing published, lock released
        TS -->> RC: exception
        RC -->> C: error (Result or exception), state unchanged
    end
```

## 3. State Machines

### 3.1 MemoryTransactionStore

```mermaid
flowchart TD
    START([created with RunState]) --> PUB[published state n]
    PUB -->|"transact called"| STAGE[staging under lock]
    STAGE -->|"op returns RunState"| NEXT([published state n+1])
    STAGE -->|"op raises or wrong type"| KEEP([state n kept, lock released])
    NEXT --> PUB
    KEEP --> PUB

    style START fill:#2196F3,color:#fff
    style PUB fill:#2196F3,color:#fff
    style STAGE fill:#FF9800,color:#fff
    style NEXT fill:#4CAF50,color:#fff
    style KEEP fill:#B71C1C,color:#fff
```

## 4. Delivery Waves (subagent-driven, `[P]` = parallel)

```mermaid
flowchart LR
    W1["Wave 1 ports [P] x3"] --> W2["Wave 2 memory adapters [P] x3"]
    W2 --> W3["Wave 3 wiring (sequential)"]
    W2 --> W4a["Wave 4 contract tests [P] x3"]
    W3 --> W4b["Wave 4 import contracts [P]"]
    W4a --> W5["Wave 5 docs [P] x4"]
    W4b --> W5
    W5 --> W6(["Wave 6 gate + final review"])

    style W1 fill:#2196F3,color:#fff
    style W2 fill:#2196F3,color:#fff
    style W3 fill:#FF9800,color:#fff
    style W4a fill:#2196F3,color:#fff
    style W4b fill:#2196F3,color:#fff
    style W5 fill:#2196F3,color:#fff
    style W6 fill:#4CAF50,color:#fff
```
