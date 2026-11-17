# Race-safe ID generation from a shared counter: research report

Date: 2026-11-17. Question: how `SequenceIdSource` (`rescue/adapters/memory/id_source.py`) keeps IDs
unique when its counter is shared by threads, and by processes, on CPython 3.14 GIL and
free-threaded builds. Race diagram: [id-source-race.md](../architecture/diagrams/id-source-race.md).

Method: deep-research workflow `wf_bc225f29-3ec`. Five search angles, 19 sources fetched, 84
claims extracted, 25 verified by three-vote adversarial checks (13 confirmed, 12 refuted). A first
run returned no usable results, so it was re-run; this report uses only the second run.

## Findings

| # | Claim | Confidence | Sources |
|---|-------|------------|---------|
| 1 | On built-in `list`, `dict` and `set`, single operations (append, pop, add, remove) are safe; compound operations are never atomic: read-modify-write (`lst[i] = lst[i] + 1`) and check-then-act (`if x in s: s.remove(x)`). | High | docs.python.org threadsafety (3.14) |
| 2 | For an ID reservation set, the membership test and the add must sit under the same lock as the counter increment. The set's own operations do not protect the pair. The pattern is inferred from rule 1. | Medium | threadsafety; free-threading HOWTO |
| 3 | The free-threading HOWTO recommends `threading.Lock` or other explicit primitives over relying on built-in internal locks, "when possible". | High | free-threading HOWTO (3.14) |
| 4 | Neither the GIL nor per-object locks make a sequence of operations atomic. | Medium | PEP 703; threadsafety |
| 5 | The per-operation guarantees on the threadsafety page are scoped to the free-threaded build. With the GIL enabled, most operations are only implicitly serialised. | High | threadsafety (3.14, 3.15) |
| 6 | `multiprocessing.Value`: `counter.value += 1` is not atomic. The fix is `with counter.get_lock(): counter.value += 1`. The lock is recursive by default. | High | docs.python.org multiprocessing |
| 7 | `multiprocessing.Lock` may be released by any process or thread. `multiprocessing.RLock` must be released by its owner, once per acquisition. | High | multiprocessing docs; local check on 3.14.10 |
| 8 | Processes attach to a `SharedMemory` block by name (`create=False`). The module states no locking or atomicity; a counter in shared memory needs its own lock. | High | shared_memory docs; local check |
| 9 | Local probe, CPython 3.14.3 and 3.12.13, GIL build, 8 threads × 200,000 increments: an inline `box[0] += 1` lost no updates; `box[0] = box[0] + one(1)` lost about 74–78%. One run per configuration. | Medium | 2022 blog; verifier probe (not reproducible from this repo) |
| 10 | A lock-protected update with a checkable invariant works as a correctness oracle. A course script shows the locked form, not the race. | Medium | single course file |
| 11 | Lock necessity: an unlocked run should show a deficit under forced interleaving and the locked run should show the exact total. A passing locked run does not prove safety. | Low | synthesis; no source states it |

**Application to `SequenceIdSource`.** The adapter already holds one lock across the counter
increment, the membership test and the reservation. That matches rules 1, 2 and 3. Claim 2 is
medium because the set rule is inferred. Our own mutation probe (lock replaced by a no-op, 8
threads × 50 draws, 5 runs) produced zero duplicates on this GIL build. That matches claim 9: the
window is narrow when no Python call sits inside the critical section.

## Refuted claims (not relied on)

Twelve claims were refuted, several for citation or paraphrase reasons. Substance that survives
is covered above. Notable refutations:

- "Multi-step logic on a set is safe without an external lock" (0–3): refuted; the page requires
  external synchronisation for multi-step operations.
- "The free-threaded build disables the GIL, so the interpreter no longer serialises thread
  execution" (0–3): refuted as stated. The fact is true; the verifier rejected the wording.
- "`multiprocessing.Value` returns a synchronized wrapper by default" (1–2): unresolved. Claim 6
  rests only on the docs quote.
- "The shared memory module states a locking guarantee" (1–2): refuted in the sense that it
  states none.
- "The GIL operates bytecode by bytecode, so it does not make a counter update atomic" (0–3):
  refuted as a citation to the 2022 blog; the substance is covered by claim 9.

## Open questions

1. Is `itertools.count.__next__` atomic on a free-threaded 3.14t build? No surviving source
   covers it; the threadsafety page has no itertools section. Do not rely on it without a test.
2. How do UUIDv7, ULID and snowflake IDs compare for uniqueness, clock skew and monotonicity? Only
   blog sources were found; none was verified against RFC 9562 or the ULID spec.
3. Does the unlocked race reproduce on a free-threaded build, and does `SequenceIdSource` lose or
   duplicate IDs there without its lock? Not run; no free-threaded interpreter is installed here.
4. Cross-process counters: which synchronisation should guard a counter in `SharedMemory`, and
   what are the POSIX cleanup rules for `track=True`? Not covered by a surviving claim.
5. `threading.RLock` release semantics were not verified; only the multiprocessing variants were.

## Caveats

- Quotes were checked against raw pages for most claims. Claim 4 (PEP 703) was checked only
  against extracted text. The pt-BR pages were paraphrased, so cite the English pages.
- All race evidence is from one run per configuration, on Windows with CPython 3.14.3 and 3.12.13.
  POSIX and free-threaded builds were not run.
- Time sensitivity: the pages were read as of 2026-11-17 (3.14.10 and 3.15.2 docs). PEP 703 dates
  from 2023 and the race blog from 2022.
