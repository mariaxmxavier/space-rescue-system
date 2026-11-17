# MemoryTransactionStore: optimistic commit timelines

Source: `rescue/adapters/memory/transaction_store.py`, method `MemoryTransactionStore.transact`.
Decision: [R3 in the 003 research](../../../specs/003-adapters-conformance/research.md).

```python
while True:
    with guard:
        base, version = state, version_number       # read snapshot
    staged, result = operation(base)                # runs in parallel, no lock held
    if staged is base:                              # read-only: publish nothing
        return result
    with guard:
        if version_number == version:               # compare-and-swap
            state, version_number = staged, version + 1
            return result
    # conflict: another commit came first; loop and run again on the newer state
```

## 1. Two requests at the same time: one commits, one retries

Start: published state at version 0.

```
time  Request A                          Request B                          published
----  ---------------------------------  ---------------------------------  -------------
t1    read snapshot (version 0)                                             v0
t2                                       read snapshot (version 0)          v0
t3    operation runs (in parallel)       operation runs (in parallel)       v0
t4    guard: 0 == 0, publish                                               v1
t5                                       guard: 0 != 1, CONFLICT            v1
t6                                       read snapshot (version 1)          v1
t7                                       operation runs again               v1
t8                                       guard: 1 == 1, publish             v2
                                         RESULT: both requests applied, in order, none lost
```

No update is lost: B's first attempt was discarded, and its second attempt started from A's
result. Under contention the cost is repeated work and drawn IDs that are not reused.

## 2. A read-only transaction publishes nothing

```
time  Reader                             Writer                             published
----  ---------------------------------  ---------------------------------  -------------
t1    read snapshot (version 1)                                             v1
t2                                       read snapshot (version 1)          v1
t3    operation returns the same state                                      v1
      -> identical object, return now (no guard, no version bump)
t4                                       guard: 1 == 1, publish             v2
```

A reader never bumps the version, so reads cannot force a writer to retry.

## 3. Why the guard lock is short

The guard is held only to read `(state, version)` and to compare and swap. The operation, which
is where the work is, runs with no lock, so two requests overlap for the whole length of their
operations. The serial part is one comparison and one assignment.
