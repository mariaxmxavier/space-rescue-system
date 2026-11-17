# Contract: Allocator

```python
Allocator = Callable[[tuple[Candidate, ...], int, Instant], AllocationResult]
```

Inputs: all candidates for one mission, unmet demand `D ≥ 0`, decision time `at`.

Every allocator MUST:

1. Return each input candidate exactly once in `allocations`, in rank order.
2. Give `seats = 0` to a candidate with a static skip reason (`static_skip_reason(c, at) is not None`).
3. Give `0 ≤ seats ≤ c.allocatable_seats`.
4. For a candidate with a held quote: `seats ∈ {0, quote.offered_seats}`.
5. Keep `Σ seats ≤ D`.
6. Be deterministic: same inputs, same output, ties broken by `ship_id`.
7. Emit at least one `TraceStep` per candidate considered, plus a final `result` step.
8. Do no I/O and read no clock.

`services/decide.py` enforces rules 1–5 and raises `DomainValidationError` on a breach.
`tests/unit/mobilisation/algorithms/test_allocator_contract.py` checks rules 1–7 for every entry in `ALLOCATORS`.

## Comparison row (services/compare.py)

| Field | Meaning |
|---|---|
| `scenario` | scenario name |
| `algorithm` | `AlgorithmName` |
| `seats_covered` | Σ seats |
| `last_seat_arrival_s` | latest arrival among chosen ships, seconds after `at`; empty if none |
| `ships_used` | count with seats > 0 |
| `unused_seats` | Σ (allocatable − seats) over chosen ships |
| `runtime_ms` | from the injected clock |
