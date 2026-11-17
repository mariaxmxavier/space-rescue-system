# Web app quickstart

## Start the API and UI

The API and static UI run separately. Allow the exact browser origin through the API's CORS setting, then start both services from the repository root:

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

1. Create a run with an application run ID and central ID. To compare strategies, first use the Experiments capability to add one or more policies and a scenario baseline, then create the run. The baseline editor provides a mission, market, ship and availability record.
2. Use the capability navigation to register a mission and fleet, publish availability or offers, then manage quotes, requests, mobilisation and responses. Each operation shows its status and complete API result.
3. Open Exploration to inspect the selected run's full committed state, mission history, decisions, communication sessions and deliveries. Load call history explicitly.
4. Use Experiments to compare the configured scenario and policy revisions. The result is labelled as a simulation and remains separate from live run state.

Open a known run ID with **Open run**. The selected run is stored in browser local storage and is reopened on the next visit. Runs and call histories are held in memory by the API and disappear when that process restarts. Repeated history reads can grow retained history substantially.
