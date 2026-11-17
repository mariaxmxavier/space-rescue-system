# Contract: import-linter changes

## Changed

| Contract | Change |
|----------|--------|
| `domain-outward` | add source `rescue.experiments.timeline` |
| `domain-io` | add source `rescue.experiments.timeline` |

## Added

```toml
[[tool.importlinter.contracts]]
name = "experiments-pure-core: Experiment models, timeline and results do not import the simulation"
type = "forbidden"
source_modules = [
    "rescue.experiments.models",
    "rescue.experiments.timeline",
    "rescue.experiments.results",
]
forbidden_modules = ["rescue.experiments.simulation"]

[[tool.importlinter.contracts]]
name = "experiments-no-bootstrap: Experiments receive their run, never import the composition root"
type = "forbidden"
source_modules = ["rescue.experiments"]
forbidden_modules = ["rescue.bootstrap", "rescue.demo"]
```

## Test updates

`tests/architecture/boundaries/test_architecture.py`:

- assert `Contracts: 13 kept, 0 broken.` (was 11);
- add both rows to the reviewed table;
- add `rescue.experiments.timeline` to `domain_sources`.
