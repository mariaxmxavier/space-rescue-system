# Contract: Communication import rules

Added to `[tool.importlinter]` in `pyproject.toml`, beside the mission contracts, and checked by `make check-architecture` (FR-010).

```toml
[[tool.importlinter.contracts]]
name = "communication-isolated: Communication imports only rescue.values and the standard library"
type = "forbidden"
source_modules = ["rescue.communication"]
forbidden_modules = [
    "rescue.mission",
    "rescue.market",
    "rescue.mobilisation",
    "rescue.experiments",
    "rescue.application",
    "rescue.adapters",
    "rescue.bootstrap",
    "rescue.demo",
]

[[tool.importlinter.contracts]]
name = "communication-layers: Communication rules build on models, never the reverse"
type = "layers"
layers = [
    "rescue.communication.rules",
    "rescue.communication.models",
]
```

The existing `domain-outward` and `domain-io` contracts stay and still cover `rescue.communication`.

Makefile: the `rescue/communication` coverage report line gains `--fail-under=100`.

Verification:
- Add `import rescue.mission` to any communication module: `make check-architecture` fails, naming `communication-isolated`.
- Add `from rescue.communication.rules import classify_delivery` to a model: it fails, naming `communication-layers`.
- Revert both.
