# Contract: Application Boundary

Rules that every file under `rescue/application/` must follow. The checks named here enforce them
in `make check-all`.

## Service shape (R3)

```python
def <use_case>(command_or_query_args, *, store: TransactionStore, <other ports used>) -> Result[T]:
    """What: …
    When called: by RescueCentral.<method>, called from <real callers>.
    Why: …
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
```

- Takes only the ports it uses, keyword-only and typed by the port ABC. It never builds an adapter.
- A mutating service does one `store.transact(operation)` and nothing outside it. An invalid input
  publishes nothing.
- It calls domain rules for every business decision and does not re-implement them.
- Shared steps come from `application/shared/`. No helper is copied into a service.
- At most 250 lines per file under `services/` (checked by `test_application_shape.py`).

## Facade shape

Each public method of `RescueCentral` has a body of exactly one statement:
`return <service>(...)`. `test_application_shape.py` checks this with an AST. The class has no
private methods.

## Allowed imports (R5)

| May import | May not import |
|---|---|
| standard library; `rescue.values`; `rescue.state`; `rescue.adapters.ports`; `rescue.mission`, `rescue.market`, `rescue.mobilisation`, `rescue.communication`; `rescue.experiments.models`, `rescue.experiments.results`; `rescue.application.*` | `rescue.adapters.memory`, `rescue.bootstrap`, `rescue.demo`, `rescue.experiments.runner`, `rescue.experiments.simulator`, `rescue.experiments.timeline`; any other module |

Enforced by the import-linter contract `application-inward` (denylist, direct and indirect), the
AST test `test_application_imports_only_allowed_modules` (allowlist, including function-local
imports) and `test_no_cycles.py`, where grimp checks that nothing upstream of
`rescue.application` is also downstream of it. The adapters allowlist no longer contains
`rescue.application.*`.

## Docstrings (FR-003)

Every module, class and function under `rescue/application/`, private helpers included, has
`What:`, `When called:`, `Why:` and `Diagram:` in that order. Each `Diagram:` path must exist. The
docstring names a non-obvious constraint, the rule it protects and its source (constitution
principle, spec FR or research entry). Inline comments are used only for steps that are not
obvious. Checked by `tests/architecture/package_layout/test_docstrings.py`.

## Diagram agreement (FR-004)

Each class, enum and command under `rescue/application/contracts/`, each service, and `RunState`
appears in APP-UML, with the same name. `RunState` fields match APP-ER. Checked by
`tests/architecture/package_layout/test_diagrams_match_code.py`, extended with the Application
namespace.
