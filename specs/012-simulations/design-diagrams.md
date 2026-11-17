# Composed mission execution

Supplement to the [plan](plan.md); records the composed timeline design, not implemented behavior.

```mermaid
flowchart TD
    A(["Choose composed profile"]) --> B["Create one mission"]
    B --> C["Queue scripted situations"]
    C --> D{"Events remain?"}
    D -->|Yes| E["Execute next virtual event"]
    E --> F{"Solver round?"}
    F -->|Yes| G["Request HTTP proposal"]
    G --> H{"Submit selected requests?"}
    H -->|Yes| I["Create proposed HTTP requests"]
    H -->|No| J["Show deferred proposal"]
    F -->|No| K["Send scripted HTTP actions"]
    I --> L["Observe outcomes and progress"]
    J --> L
    K --> L
    L --> M["Check situation evidence"]
    M --> N{"Mission complete?"}
    N -->|Yes| O["Suppress new request submissions"]
    N -->|No| D
    O --> D
    D -->|No| P["Check final state and coverage"]
    P --> Q(["Report scenario result"])
    E -->|Operational failure| R["Report failed event"]
    L -->|Unexpected outcome| R
    M -->|Bound exceeded| R
    R --> Q
```

Each profile has one mission and multiple situation recipes (FR-001/002/010). Proposal/submission are distinct (FR-003), observations stream continuously (FR-004/005), and completion does not discard remaining events (FR-008). Final success requires evidence for every included situation and its expected final state (FR-006/009). Failure preserves the observed prefix. all12/all11/all10/baseline share the loop; they do not launch separate missions for each situation.
