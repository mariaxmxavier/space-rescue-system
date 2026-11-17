# Contract: run factory injection

## `simulate`

```python
def simulate(
    scenario: RescueScenario,
    policy: MobilisationPolicy,
    run_id: str,
    *,
    start_run: StartRun,
) -> RunSnapshot
```

- Imported from `rescue.experiments.simulation`.
- `start_run` is keyword-only and required; a missing argument is a `TypeError`.
- A non-callable `start_run` raises `DomainValidationError`.
- It is called once per simulation, exactly as `new_run` is called today:
  `start_run(run_id, f"{run_id}-central", policies=(policy,), scenarios=(scenario,), reserved_ids=baseline_identity_ids(baseline))`.

## Ports (`rescue/experiments/simulation/ports/`, one Protocol per file)

| Port | Members the runner uses |
|------|-------------------------|
| `StartRun` | `__call__(application_run_id, central_id, *, policies, scenarios, reserved_ids) -> RunHandle` |
| `RunHandle` | `store: TransactionStore` (`transact`, `snapshot`), `id_source: IdSource` (`next_id`), `central: SimulationCentral` |
| `SimulationCentral` | `mobilise`, `create_request`, `publish_availability`, `expire_request`, `record_response` (commands and `Result` from `rescue.application.contracts`) |

`rescue.bootstrap.new_run` and `RunContext` satisfy these ports structurally; neither changes.

## Callers

| Caller | Passes |
|--------|--------|
| `RescueCentral.compare` | `self.start_run`, a new required dataclass field |
| `rescue.bootstrap.new_run` | builds `RescueCentral(..., start_run=new_run)` |
| `rescue.demo` | `start_run=new_run` |
| tests (`test_experiments`, `test_communication`, `test_resilience`) | `start_run=new_run` |
