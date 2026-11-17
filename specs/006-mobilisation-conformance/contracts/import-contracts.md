# Contract: Import rules added to `pyproject.toml`

| Name | Type | Rule |
|---|---|---|
| `mobilisation-peers-one-way` | forbidden | `rescue.mission`, `rescue.market` → must not import `rescue.mobilisation` |
| `mobilisation-allowed-imports` | forbidden | `rescue.mobilisation` → must not import `rescue.communication`, `rescue.experiments`, `rescue.application`, `rescue.adapters`, `rescue.bootstrap`, `rescue.demo` |
| `mobilisation-layers` | layers | `rescue.mobilisation.services` > `rescue.mobilisation.algorithms` > `rescue.mobilisation.models` |
| `mobilisation-solver-isolated` | forbidden | `rescue.mobilisation.models`, `rescue.mobilisation.services` → must not import `ortools` |

The existing `domain-outward` and `domain-io` contracts keep covering `rescue.mobilisation`.
Each new contract is proved by one seeded violation (SC-004) in `tests/architecture/boundaries/`.
