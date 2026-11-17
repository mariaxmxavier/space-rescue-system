# SequenceIdSource race: ASCII timelines

Source: `rescue/adapters/memory/id_source.py`, method `SequenceIdSource.next_id`.

```python
normalized_kind = normalize_id(kind)
with self._lock:
    while True:
        self._counter += 1
        candidate = f"{normalized_kind}-{self._counter:08d}"
        if candidate not in self._reserved_ids:
            self._reserved_ids.add(candidate)
            return candidate
```

`self._counter += 1` is a read, an add and a write. The membership test and `add` are a second
read-then-write on `self._reserved_ids`. Without the lock, both pairs can interleave.

## 1. Without the lock: two threads return the same ID

Start state: `counter = 5`, `reserved = {}`, kind `request`.

```
time  Thread A                             Thread B                             shared state
----  -----------------------------------  -----------------------------------  ---------------------------
t1    read counter (5)                                                          counter = 5
t2                                         read counter (5)                     counter = 5
t3    write counter (6)                                                         counter = 6
t4                                         write counter (6)                    counter = 6   LOST UPDATE
t5    candidate = request-00000006                                              counter = 6
t6                                         candidate = request-00000006         counter = 6
t7    check: not in reserved -> True                                            reserved = {}
t8                                         check: not in reserved -> True       reserved = {}   CHECK PASSED TWICE
t9    add request-00000006; return                                              reserved = {request-00000006}
t10                                        add request-00000006; return          reserved = {request-00000006}
                                                                                 RESULT: both callers hold request-00000006
```

Two failure points: the counter update at t3-t4 (both threads increment from 5), and the
check-then-add at t7-t10 (both threads pass the check before either adds). Either one alone
produces a duplicate.

## 2. With the lock: the same two calls serialise

```
time  Thread A                             Thread B                             shared state
----  -----------------------------------  -----------------------------------  ---------------------------
t1    acquire lock                                                              lock = held by A
t2    read counter (5), write 6                                                  counter = 6
t3    candidate = request-00000006                                               counter = 6
t4    check and add request-00000006                                             reserved = {request-00000006}
t5    return; release lock                                                      lock = free
t6                                         acquire lock                         lock = held by B
t7                                         read counter (6), write 7            counter = 7
t8                                         candidate = request-00000007         counter = 7
t9                                         check and add request-00000007       reserved = {..06, ..07}
t10                                        return; release lock                 lock = free
                                                                                 RESULT: two distinct IDs
```

## Why the race is hard to see on CPython 3.14 (GIL build)

A thread switch happens only at certain bytecode boundaries. In the critical section above there
is no call or backward jump between the read and the write of `_counter`. A probe on this machine
(8 threads x 50 draws, 5 runs, lock replaced by a no-op) produced zero duplicates. On a
free-threaded build, threads run in parallel with no global lock, so the interleaving in
sections 1 is possible. The lock is therefore required for correctness even where the race is
rare to observe. See `tests/integration/adapters/memory/test_id_source.py` for the test and its
known limit.
