# Tasks: Rescue HTTP API

**Input**: [spec](spec.md), [plan](plan.md), [contract](contracts/http-api.md), [data model](data-model.md), [research](research.md)

`[P]` marks tasks that may run concurrently only after their stated prerequisites are complete. Each writer owns only the paths named in their task. The parent integrates and verifies the combined changes. Apply the repository's existing layout and import contracts; framework types and business decisions must not enter the domain or application services. No commit without authorisation.

## Phase 1: Setup

- [ ] T001 Pin FastAPI 0.163.1 and exact compatible server and HTTP test-client versions in `pyproject.toml`, update `uv.lock`, and verify installation with `make install`.

## Phase 2: Foundation

- [ ] T002 Define the shared outer-layer run registry and per-run lock in `rescue/api/runtime.py`: unique client-supplied run IDs, isolated `new_run` contexts including policies and scenarios, in-memory lifetime, and ordered complete call entries; do not import FastAPI into business layers. Depends on T001.
- [ ] T003 [P] Implement lossless conversion and input validation in `rescue/api/codec.py` for nested dataclasses, enums, tuples, null and decimal strings, preserving every field; reject invalid and unknown fields. Depends on T001.
- [ ] T004 [P] Define the explicit 22-operation allowlist and argument schemas in `rescue/api/operations.py` from `rescue/application/central.py`, including scalar arguments and nested policy, scenario and command values; no arbitrary method dispatch. Depends on T001 and the contract, not T002 or T003.

## Phase 3: User Story 1 — Operate a rescue (P1)

**Goal**: Create isolated runs and invoke every application operation with complete results.

**Independent test**: Drive the demo rescue through HTTP and compare results, including rejection, with the application; confirm 10 seats and no pending seats.

- [ ] T005 [P] [US1] Write focused HTTP tests in `tests/integration/api/http/test_operations.py` for run creation with policy/scenario inputs, representative operation results and invalid input; assert complete status/value/reason and unchanged state on rejection. Run before T007 and confirm failure. Depends on T001.
- [ ] T006 [P] [US1] Implement local origin enforcement and browser CORS configuration in `rescue/api/origins.py`, rejecting untrusted state-changing origins while accepting local CLI requests without Origin; bind server to loopback. Depends on T001.
- [ ] T007 [US1] Wire creation and operation routes in `rescue/api/app.py` and `rescue/api/__init__.py`, using T002–T004 and T006; return 201/200/400/404/409 as specified, expose schemas and preserve application behavior. Make T005 pass. Depends on T002–T006.

## Phase 4: User Story 2 — View the run (P1)

**Goal**: Expose the latest committed run and complete ordered call history, including reads.

**Independent test**: Execute partial acceptance and refusal, then compare state and history with the run; two history reads show that the second contains the first full response.

- [ ] T008 [P] [US2] Write focused tests in `tests/integration/api/http/test_history.py` for isolated run state, invalid-call recording, concurrent ordering and two complete history reads, including the prior response; run before T010 and confirm failure. Depends on T001.
- [ ] T009 [P] [US2] Implement read-only committed snapshot retrieval in `rescue/api/state.py`, retaining every `RunState` field and using a read-only transaction through the existing store interface. Depends on T002 and T003.
- [ ] T010 [US2] Add state/history routes and request recording in `rescue/api/app.py` using T002 and T009; serialize each known-run call, record its input, status and complete response after completion, and ensure a history read snapshots earlier entries before recording itself. Include malformed known-run calls; creation and unknown runs have no existing history. Make T008 pass. Depends on T007–T009.

## Phase 5: Polish and verification

- [ ] T011 [P] Document exact startup, origin configuration, API discovery, in-memory lifetime and history growth in `README.md`, and update `specs/011-http-api/quickstart.md` with runnable demo requests. Depends on T007 and T010.
- [ ] T012 [P] Extend architecture checks in `pyproject.toml` and `tests/architecture/boundaries/test_architecture.py` to keep `rescue.api` and FastAPI outside domain/application policy without weakening existing contracts. Depends on T007 and T010.
- [ ] T013 Run focused tests, `make check-all`, the HTTP quickstart and `uv run python -m rescue.demo`; record outcomes in `specs/011-http-api/validation.md`. Depends on T011 and T012.

## Dependencies and parallel dispatch

- T001 → T002, T003 and T004 in parallel. T005 and T006 may also start after T001; their paths do not overlap foundation work.
- T007 waits for T002–T006. In parallel after T002 and T003, dispatch T008 and T009; T010 waits for T007–T009.
- T011 and T012 run in parallel after T010; T013 follows both. Writers never overlap `rescue/api/app.py`.
- US2 can be tested independently with a pre-populated run fixture; end-to-end acceptance uses US1 as well.
- MVP is US1 after T007. Deliver US2 and the final checks before declaring the complete feature done.
