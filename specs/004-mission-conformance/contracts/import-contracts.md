# Contract: Mission import rules

Added to `[tool.importlinter]` in `pyproject.toml`; checked by `make check-architecture` (FR-008).

```toml
[[tool.importlinter.contracts]]
name = "mission-isolated: Mission imports only rescue.values and the standard library"
type = "forbidden"
source_modules = ["rescue.mission"]
forbidden_modules = [
    "rescue.market",
    "rescue.mobilisation",
    "rescue.communication",
    "rescue.experiments",
    "rescue.application",
    "rescue.adapters",
    "rescue.bootstrap",
    "rescue.demo",
]

[[tool.importlinter.contracts]]
name = "mission-layers: Mission rules build on models, never the reverse"
type = "layers"
layers = [
    "rescue.mission.rules",
    "rescue.mission.models",
]
```

The existing `domain-outward` and `domain-io` contracts stay and still cover `rescue.mission`.

Makefile: the `rescue/mission` coverage report line gains `--fail-under=100` (FR-009).

Verification: add `import rescue.market` to any mission module → `make check-architecture` fails
naming `mission-isolated`; add `from rescue.mission.rules import progress` to a model → fails
naming `mission-layers`.
