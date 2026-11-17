# Validate composed mission timelines

This guide specifies the target behavior after implementation. Commands are not evidence that simulations already exist.

## Prerequisites

Use uv 0.13.8 and Python 3.14.10, then run make install. The nested API payload repair in the tasks must pass before running timelines. No new server is launched by the simulation command.

In a separate terminal, start the existing local API:

```powershell
uv run uvicorn rescue.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

Then:

```powershell
uv run python -m simulations list
uv run python -m simulations run all12
uv run python -m simulations run all11
uv run python -m simulations run all10
uv run python -m simulations run baseline
uv run python -m simulations run --all --base-url http://127.0.0.1:8000
```

Each run creates exactly one mission with a fresh namespace. all12 must visibly show temporary shortfall, subsequent solver rounds, request closures, rejected/ignored deliveries, and final completion10/0. Its summary must show12/12 observed situations; all11 shows11/11, all10 shows10/10. Repeat all12 without restarting the server; business expectations stay the same while identities change. Missing evidence is failure even if ten seats were confirmed.

Confirm the CLI does not stop at the first complete progress snapshot: the t=26 replay must still be shown in all12/all11 and must not add confirmed seats. Verify stdout distinguishes virtual time, session sequence and batch submission order. Details are in the [CLI contract](contracts/simulation.md) and [timeline](contracts/timeline.md).

## Checks

```powershell
make check-all
uv run pytest tests/integration/api/http/test_nested_commands.py
uv run pytest tests/unit/simulations tests/integration/simulations tests/architecture/simulations
uv run pytest tests/e2e/simulations/timeline -m live_http --simulation-base-url http://127.0.0.1:8000
```

The e2e fixture uses that already-running server and must fail clearly if explicitly requested without its URL. Register live_http; default gates explicitly select not live_http, so they require no listening server. The default make check-all exercises full composed timelines through an injected TestClient; explicit live selection verifies real loopback transport. Keep the existing demo check green. Verify per-layer simulations branch coverage >=80%, with all existing rescue coverage thresholds retained.

Unknown profile -> exit2 before network access. Unreachable server -> exit1 and no invented mission outcome. Force a fake outcome mismatch in unit tests -> failed event/expected/observed evidence and exit1. Do not add a CLI fault switch merely to test failures.
