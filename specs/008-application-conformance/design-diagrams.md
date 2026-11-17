# Design Diagrams: 008 Application Conformance

**Change**: 008-application-conformance | **Design**: [plan.md](plan.md), [data-model.md](data-model.md), [research.md](research.md)

These are feature-level design views. The maintained UML and ER views of the application live in
`docs/architecture/diagrams/rescue-domain-model/namespaces/Application/` (R10).

## Color Conventions

| Flow Type | Color | Hex |
|-----------|-------|-----|
| Submission / happy-path | blue | `#2196F3` |
| Validation / processing | amber | `#FF9800` |
| Safety / blocking / rejection | red | `#F44336` |
| Routing / delivery / success | green | `#4CAF50` |
| Error / failure | crimson | `#B71C1C` |

Node styles: facade and services `fill:#E3F2FD,stroke:#1565C0` (bold); ports and adapters
(service objects) `fill:#FFF3E0,stroke:#EF6C00`; domain and data `fill:#E8EAF6,stroke:#7986CB`
(rounded); out of scope is dashed grey.

## 1. Component Dependencies (target)

Imports point inwards. `-->` is a runtime call to an injected dependency, `-.->` (italic) is a
compile-time use of a domain or data type, and `==>` is a facade-to-service delegation. The red
edge shows the cycle that is removed.

```mermaid
flowchart TD
    subgraph ext["Out of Scope (callers and 009)"]
        DEMO(["demo"])
        RUNNER(["experiments.runner"])
    end

    subgraph root["Composition root"]
        BOOT["bootstrap.new_run"]
    end

    subgraph app["rescue.application"]
        CENTRAL[["RescueCentral (facade)"]]
        SVC[["services/* (19 use cases)"]]
        SHARED["shared/* (13 helpers)"]
        CONTRACTS(["contracts/* (Result, 14 commands, enums)"])
    end

    subgraph ports["rescue.adapters.ports"]
        PSTORE["TransactionStore"]
        PIDS["IdSource"]
        PCLOCK["Clock"]
        PSIM["Simulator (new)"]
    end

    subgraph impl["Adapters"]
        MEM["adapters.memory.*"]
        RSIM["experiments.simulator.RunnerSimulator"]
    end

    subgraph inner["Inner packages"]
        STATE(["rescue.state.RunState"])
        DOMAIN(["mission / market / mobilisation / communication / experiments.models"])
        VALUES(["rescue.values (is_deeply_immutable)"])
    end

    DEMO -.->|"1. new_run"| BOOT
    BOOT -->|"2. builds"| MEM
    BOOT -->|"3. builds"| RSIM
    BOOT -->|"4. injects ports"| CENTRAL
    CENTRAL ==>|"5. delegate"| SVC
    SVC -->|"6. transact / snapshot"| PSTORE
    SVC -->|"7. next_id"| PIDS
    SVC -->|"8. simulate"| PSIM
    SVC -->|"uses"| SHARED
    SVC -.->|"_accepts / returns_"| CONTRACTS
    SVC -.->|"_calls rules_"| DOMAIN
    SHARED -.->|"_reads_"| STATE
    MEM -.->|"_implements_"| PSTORE
    MEM -.->|"_implements_"| PIDS
    MEM -.->|"_implements_"| PCLOCK
    RSIM -.->|"_implements_"| PSIM
    RSIM -.->|"lazy import (until 009)"| RUNNER
    RUNNER -.->|"new_run"| BOOT
    MEM -.->|"_stores_"| STATE
    STATE -.->|"_composes_"| DOMAIN
    STATE -.->|"_validates with_"| VALUES
    SVC -. "removed: function-local import" .-x RUNNER

    style DEMO stroke-dasharray:5 5,stroke:#999,fill:#f5f5f5,color:#333
    style RUNNER stroke-dasharray:5 5,stroke:#999,fill:#f5f5f5,color:#333
    style BOOT fill:#FFF3E0,stroke:#EF6C00,color:#333
    style CENTRAL fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#333
    style SVC fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#333
    style SHARED fill:#FFF3E0,stroke:#EF6C00,color:#333
    style CONTRACTS fill:#E8EAF6,stroke:#7986CB,color:#333
    style PSTORE fill:#FFF3E0,stroke:#EF6C00,color:#333
    style PIDS fill:#FFF3E0,stroke:#EF6C00,color:#333
    style PCLOCK fill:#FFF3E0,stroke:#EF6C00,color:#333
    style PSIM fill:#FFF3E0,stroke:#EF6C00,color:#333
    style MEM fill:#FFF3E0,stroke:#EF6C00,color:#333
    style RSIM fill:#FFF3E0,stroke:#EF6C00,color:#333
    style STATE fill:#E8EAF6,stroke:#7986CB,color:#333
    style DOMAIN fill:#E8EAF6,stroke:#7986CB,color:#333
    style VALUES fill:#E8EAF6,stroke:#7986CB,color:#333

    linkStyle 0,1,2,3 stroke:#2196F3,stroke-width:2px
    linkStyle 4,5,6,7 stroke:#4CAF50,stroke-width:2px
    linkStyle 16,17 stroke:#FF9800,stroke-width:2px
    linkStyle 21 stroke:#F44336,stroke-width:2px
```

## 2. Sequence Diagram: `accept_quote` through the facade

This shows the happy path, replay, rejection, and a domain error inside the transaction (nothing
is published).

```mermaid
sequenceDiagram
    participant C as Caller
    participant F as RescueCentral
    participant S as services.quotes.accept_quote
    participant T as TransactionStore
    participant H as shared (command_entry, open_request)
    participant D as mission_rules / market_rules
    participant I as IdSource

    rect rgb(227,242,253)
        Note over C,I: Happy path (applied)
        C ->> F: accept_quote(AcceptQuote)
        F ->> S: accept_quote(command, store=, id_source=)
        S ->> T: transact(operation)
        T ->> H: command_entry(state, command_id) → None
        H ->> I: next_id("request"), next_id("event")
        H ->> D: add_request, transfer_quote
        D -->> H: updated Mission, B3Market
        H -->> T: (new RunState, Result applied)
        T -->> S: publish new state, return Result
        S -->> F: Result applied
        F -->> C: Result applied
    end

    rect rgb(232,245,233)
        Note over C,I: Replay (same command_id and payload)
        C ->> F: accept_quote(same command)
        F ->> S: accept_quote(...)
        S ->> T: transact(operation)
        T ->> H: command_entry → existing entry
        H -->> T: (same state, Result replayed + original value)
        T -->> C: Result replayed, no new IDs drawn
    end

    rect rgb(255,235,238)
        Note over C,I: Rejection (expired quote)
        C ->> F: accept_quote(expired quote)
        F ->> S: accept_quote(...)
        S ->> T: transact(operation)
        T ->> H: open_request guards
        H -->> T: (same state, Result rejected/expired_quote)
        T -->> C: Result rejected, nothing published
    end

    rect rgb(255,205,210)
        Note over C,I: Domain error inside the transaction
        C ->> F: accept_quote(invalid seats)
        F ->> S: accept_quote(...)
        S ->> T: transact(operation)
        T ->> D: add_request
        D -->> T: raises DomainValidationError
        T -->> C: Result rejected/error_reason_for(error), state unchanged
    end
```

## 3. State Machine: `Result.status` per service call

```mermaid
flowchart TD
    START([command received]) --> VALIDATE[normalise input at boundary]
    VALIDATE -->|"invalid input or domain error"| REJECTED([rejected: state unchanged])
    VALIDATE --> REPLAY{command_id already applied?}
    REPLAY -->|"same payload"| REPLAYED([replayed: original value])
    REPLAY -->|"different payload"| REJECTED
    REPLAY -->|"no"| CLOSED{request already closed?}
    CLOSED -->|"yes"| IGNORED([ignored: closed_request])
    CLOSED -->|"no"| APPLY[call domain rules inside transact]
    APPLY -->|"success"| APPLIED([applied: new state published])
    APPLY -->|"rule rejects"| REJECTED

    style START fill:#2196F3,color:#fff
    style VALIDATE fill:#FF9800,color:#fff
    style REPLAY fill:#FF9800,color:#fff
    style CLOSED fill:#FF9800,color:#fff
    style APPLY fill:#FF9800,color:#fff
    style APPLIED fill:#4CAF50,color:#fff
    style REPLAYED fill:#4CAF50,color:#fff
    style IGNORED fill:#4CAF50,color:#fff
    style REJECTED fill:#B71C1C,color:#fff
```

Not every service has every branch: only command-ID services replay, and only request-closing
services return `ignored`.

## 4. Target Layout

```mermaid
flowchart LR
    subgraph application["rescue/application"]
        C["central.py"]
        subgraph contracts["contracts/"]
            CR["result.py · result_status.py · error_reason.py · snapshots.py"]
            CC["commands/ (14 files)"]
        end
        subgraph services["services/"]
            S1["missions/ (3)"]
            S2["fleet/ (3)"]
            S3["quotes/ (5)"]
            S4["requests/ (4)"]
            S5["mobilisation/ (2)"]
            S6["communication/ (1)"]
            S7["comparison/ (1)"]
        end
        SH["shared/ (13 files)"]
    end
    ST["rescue/state/run_state.py"]
    SIM["rescue/adapters/ports/simulator.py"]

    C --> services
    services --> SH
    services --> contracts
    services --> SIM
    SH --> ST

    style C fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#333
    style ST fill:#E8EAF6,stroke:#7986CB,color:#333
    style SIM fill:#FFF3E0,stroke:#EF6C00,color:#333
```

## 5. Wave Dispatch (subagent-driven development)

`[P]` waves fan out to implementers that own disjoint files. The controller gates every wave with
`make check-all`.

```mermaid
flowchart TD
    W0([0 Baseline + rebase gate]) --> W1a
    subgraph W1a["1a [P]"]
        A1["values.is_deeply_immutable"]
        A2["ports/simulator.py"]
    end
    W1a --> W1b["1b rescue/state/ (sequential)"]
    W1b --> W2
    subgraph W2["2 [P] contracts/"]
        B1["core + __init__"]
        B2["commands/"]
    end
    W2 --> W3
    subgraph W3["3 [P] shared/"]
        C1["lookups"]
        C2["request guards"]
        C3["transitions"]
    end
    W3 --> W4
    subgraph W4["4 [P] services/ (one per folder)"]
        D1["missions"]
        D2["fleet"]
        D3["quotes"]
        D4["requests"]
        D5["mobilisation"]
        D6["communication"]
        D7["comparison"]
    end
    W4 --> W5["5 facade + wiring (sequential)"]
    W5 --> W6
    subgraph W6["6 [P] checks"]
        E1["import contracts + cycle test"]
        E2["package_layout + shape test"]
        E3["Makefile coverage"]
    end
    W6 --> W7
    subgraph W7["7 diagrams and docs"]
        F1["[P] UML + ER"]
        F2["[P] README, docs index, roadmap"]
        F3["docstring Diagram: sweep (after F1)"]
    end
    W7 --> W8([8 Gate: check-all, demo cmp, seeded violations])

    style W0 fill:#2196F3,color:#fff
    style W8 fill:#4CAF50,color:#fff
    style W1b fill:#FF9800,color:#fff
    style W5 fill:#FF9800,color:#fff
```
