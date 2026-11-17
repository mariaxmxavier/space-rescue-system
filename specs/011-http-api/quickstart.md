# Quickstart validation

Install dependencies and run the full project gate:

```powershell
make install
make check-all
```

Start the API in another terminal:

```powershell
uv run uvicorn rescue.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs`. Create a run and register a mission:

```powershell
$run = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/runs -ContentType 'application/json' -Body '{"application_run_id":"RUN-LOCAL","central_id":"CENTRAL-LOCAL"}'
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/runs/RUN-LOCAL/operations/register_mission -ContentType 'application/json' -Body '{"command":{"mission_id":"MISSION-LOCAL","station_name":"North Station","people_count":2,"created_at":"0"}}'
Invoke-RestMethod -Uri http://127.0.0.1:8000/runs/RUN-LOCAL/state
Invoke-RestMethod -Uri http://127.0.0.1:8000/runs/RUN-LOCAL/history
```

Confirm the operation result includes `status`, `value` and `reason`; the state contains the mission; and history contains the completed calls. Read history again and confirm the response contains the first history response. Runs and call history are process-local and are cleared when the server stops. Repeated history reads retain increasingly large responses.
