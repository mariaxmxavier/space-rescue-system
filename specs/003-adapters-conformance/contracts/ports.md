# Port Contracts

What any adapter of a port must do. The executable form of each contract is the matching
`check_<port>_contract` function in `tests/integration/adapters/contracts/`. TS-4 (concurrent reads)
is not part of that check: it is proven for the memory store by
`tests/integration/adapters/memory/test_memory.py::test_concurrent_read_observes_one_complete_published_snapshot`,
because one sequential call cannot show it.

## TransactionStore

| # | Given | When | Then |
|---|---|---|---|
| TS-1 | a store over state S | `transact(op)` returns `(S', r)` | returns `r`; `snapshot()` is `S'`; S is unchanged |
| TS-2 | a store over state S | `op` raises | the exception propagates; `snapshot()` is still S |
| TS-3 | a store over state S | `op` returns a non-`RunState` | `TypeError`; `snapshot()` is still S |
| TS-4 | a write in progress | another thread calls `snapshot()` | it sees S or S' in full, never a mix |

Seeded fault: a store that publishes on exception fails TS-2.

## Clock

| # | When | Then |
|---|---|---|
| CL-1 | `now()` | a finite `Decimal` ≥ 0 |
| CL-2 | `ZeroClock().now()`, repeated | always `0` |

Seeded fault: a clock that returns `-1` fails CL-1.

## IdSource

| # | When | Then |
|---|---|---|
| ID-1 | 150 draws across two kinds from one source | no ID repeats |
| ID-2 | `SequenceIdSource(reserved)` | never returns a reserved ID |

Seeded fault: a source that always returns `<kind>-1` fails ID-1.
