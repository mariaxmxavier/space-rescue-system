# Data Model: Adapters Conformance

No new domain data. This feature changes where the run-state boundary lives, not what the run
state holds.

## Ports (abstract, `rescue/adapters/ports/`)

| Port | Operations | Invariant |
|---|---|---|
| `TransactionStore` | `transact(operation) -> T` (abstract); `snapshot() -> RunState` (concrete) | publishes only when `operation` returns `(RunState, result)` without raising |
| `Clock` | `now() -> Instant` (abstract) | a finite, non-negative `Decimal` |
| `IdSource` | `next_id(kind) -> Id` (abstract) | never repeats within one run |

## Adapters (`rescue/adapters/memory/`)

| Adapter | Implements | State | Validation |
|---|---|---|---|
| `MemoryTransactionStore` | `TransactionStore` | one `RunState` reference, a version number and a short guard `threading.Lock`; operations run in parallel and publish by compare-and-swap (R3) | rejects a non-`RunState` initial state (`TypeError`) and a non-`RunState` staged state (`TypeError`, nothing published) |
| `ZeroClock` | `Clock` | none | always `Decimal("0")` |
| `SequenceIdSource` | `IdSource` | counter, set of taken IDs, lock | normalises `kind`; skips reserved IDs; format `<KIND>-<8-digit counter>` |

## Relationships

- `RescueCentral` holds one of each port; it only knows the port types.
- `bootstrap.new_run` builds one `MemoryTransactionStore` per run. It uses `ZeroClock` and
  `SequenceIdSource(reserved_ids)` unless the caller passes its own clock or ID source.
- A caller-supplied clock or ID source does not have to inherit from the port; any object with
  `now()` / `next_id()` is accepted (clarification 2026-11-16).
- `RunState` stays in `rescue/application/state.py` until spec 008 (FR-010).

## Store lifecycle

`created(initial_state)` → `published(state_n)` → on success `published(state_n+1)`; on an
exception or a wrong type, it stays `published(state_n)` and the lock is released.
