# Implementation Plan: Rescue HTTP API

**Branch**: `011-http-api` (planned) | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

## Summary

Add a local FastAPI entrypoint over the existing application. Expose all facade calls, a committed state read and per-run call history. Preserve complete history responses, including reads.

## Technical Context

- Python 3.14.10, uv 0.13.8, FastAPI 0.163.1; pin the compatible HTTP server and test client exactly when resolving the lockfile.
- One process on loopback; in-memory run registry and history. Restart clears both.
- Reuse `new_run`, `RescueCentral`, immutable `RunState`, and pytest; preserve domain behavior.
- Local development scale; no throughput target. Full history responses can grow exponentially and exhaust memory.
- See [research](research.md), [data model](data-model.md), [contract](contracts/http-api.md) and [quickstart](quickstart.md).

## Constitution Check

**Before and after design: pass.** Delegate rescue decisions to existing services and preserve transaction semantics. Verify representative accounting and failures over HTTP, then run the full gate and demo. Keep transport outside domain and adapter import contracts. Pin dependencies exactly.

## Project Structure

- `rescue/api/`: app factory, explicit operation registry and JSON conversion, in-memory run and history management.
- `rescue/bootstrap.py`: reuse `new_run` without changing domain semantics.
- `pyproject.toml`, `uv.lock`, `README.md`: pinned dependencies, execution and interface documentation.
- `tests/integration/api/http/test_api.py`: focused HTTP scenarios; existing tests remain authoritative for domain rules.

## Implementation sequence

1. Add pinned dependencies and a local app factory. Build run registry, strict request decoding and explicit facade operation map, with all 22 operations and creation-time policies/scenarios. Document schemas and the contract. Verify a complete demo rescue through HTTP and full result fields.
2. Add committed state reads and per-run call recording with serialized processing per run. Record malformed input, domain rejection, reads and history reads; preserve complete prior responses. Verify isolation, ordering, invalid input, repeated history reads and allowed/disallowed browser origins.
3. Document startup and assumptions; run focused tests, `make check-all` and `uv run python -m rescue.demo`. Avoid tests duplicating domain rules or unnecessary abstractions.

## Review focus

- Every facade operation and nested command type has an explicit schema; no arbitrary method dispatch.
- Decimal values round-trip exactly; optional values, enums, tuples and nested objects retain information.
- A known run's malformed request is recorded even when validation fails; unknown-run requests cannot be attached to a run.
- Concurrent calls have one per-run completion order; history reads include earlier completed entries and record their response afterwards.
- Loopback binding and explicit browser origin checks protect state-changing requests; CORS alone does not block hostile requests.
