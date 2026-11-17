# Contract: Declared import rules

Declared in `pyproject.toml` under `[tool.importlinter]`, `root_package = "rescue"`,
`include_external_packages = true`.

| Id | Sources | Forbidden | Indirect allowed | Replaces in `test_architecture.py` |
|---|---|---|---|---|
| `domain-outward` | `rescue.mission`, `rescue.market`, `rescue.mobilisation`, `rescue.communication`, `rescue.experiments.models`, `rescue.experiments.results` | `rescue.application`, `rescue.adapters`, `rescue.bootstrap` | no | `test_domain_capabilities_do_not_import_application_adapters_or_bootstrap`; outward-import half of `test_experiment_models_and_results_remain_pure` and of `test_domain_capabilities_do_not_read_environment_or_use_io_clocks_or_network` |
| `domain-io` | same as above | `os`, `time`, `socket`, `urllib`, `http`, `subprocess`, `sqlite3`, `requests`, `httpx`, `sqlalchemy` | no | I/O-import half of the two tests above |
| `application-no-memory` | `rescue.application` | `rescue.adapters.memory` | **yes**, until 008/009 break the `central → runner → bootstrap` cycle | `test_application_does_not_import_concrete_memory_adapter` (module part) |

## Stays in `test_architecture.py`

- Forbidden calls in domain packages (`open`, `sleep`, `time`, `datetime.now`, `os.getenv`, …).
- `os.environ` / `os.environb` attribute reads.
- `MemoryTransactionStore` imported by name into `application` (a name check, not a module check).

## Verification (SC-004)

For each contract, plant one forbidden import in a scratch edit, run `make check-architecture`,
see it fail naming the contract, then revert.
