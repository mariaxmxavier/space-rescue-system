# Web app quickstart

## Start the API and UI

The API and static UI run separately. Allow the exact browser origin through the API's CORS setting, then start both services from the repository root:

Linux/macOS:

```bash
SPACE_RESCUE_ALLOWED_ORIGINS=http://127.0.0.1:8001 uv run uvicorn rescue.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

Windows PowerShell:

```powershell
$env:SPACE_RESCUE_ALLOWED_ORIGINS = "http://127.0.0.1:8001"
uv run uvicorn rescue.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
python -m http.server 8001 --bind 127.0.0.1 --directory web
```

Open `http://127.0.0.1:8001/?api=http%3A%2F%2F127.0.0.1%3A8000`. The `api` query parameter selects the API origin and is remembered by the browser. The default API origin is `http://127.0.0.1:8000`.

## Use the console

The default page is the simulation viewer. The baseline is prepared automatically and starts **paused at the beginning**. Choose a case to prepare a fresh execution:

| Case | Situations |
| --- | --- |
| baseline | Full confirmations, ten seats across three ships |
| all10 | Ten situations, including partial responses, closures, availability changes and unreliable communication |
| all11 | Adds duplicate-message replay |
| all12 | Adds competing concurrent requests |

Use Play/Pause, playback speed, previous/next event, or the labelled timeline and time input to inspect any point. All panels show the same committed snapshot. Between events, the last committed state remains visible. Individual event navigation distinguishes events at the same logical time. Seeking reads retained snapshots; it never repeats rescue operations. Completion and the case's evidence verification are separate results, and post-completion events remain inspectable.

Expand **Advanced workspace** for every operation below. A direct link with `?workspace=manual` opens that workspace immediately; combine it with `&api=http%3A%2F%2F127.0.0.1%3A8000` to select an API origin. The manual workspace displays the current live run, separately from the simulation viewer's historical cursor.

1. Create a run with an application run ID and central ID. To compare strategies, first use the Experiments capability to add one or more policies and a scenario baseline, then create the run. The baseline editor provides a mission, market, ship and availability record.
2. Use the capability navigation to register a mission and fleet, publish availability or offers, then manage quotes, requests, mobilisation and responses. Each operation shows its status and complete API result.
3. Open Exploration to inspect the selected run's full committed state, mission history, decisions, communication sessions and deliveries. Load call history explicitly.
4. Use Experiments to compare the configured scenario and policy revisions. The result is labelled as a simulation and remains separate from live run state.

Open a known run ID with **Open run**. The selected run is stored in browser local storage and is reopened on the next visit. Runs and call histories are held in memory by the API and disappear when that process restarts. Repeated history reads can grow retained history substantially.

## Verify locally

```bash
make install
uv run playwright install chromium
make check-all
uv run pytest tests/e2e/web tests/integration/api/simulations
```

The browser fixtures start their own isolated API/static servers. No separately running API is needed for this suite. Execution uses the same public operation JSON contract as external clients, including the codec, authoritative rules and recorded call history; simulation state is not generated in JavaScript.
