"""Run state and call history behavior for feature 011."""

from fastapi.testclient import TestClient

from rescue.api.app import create_app


def test_state_and_history_include_calls_and_history_read_response():
    client = TestClient(create_app())
    client.post("/runs", json={"application_run_id": "RUN-H", "central_id": "CENTRAL-H"})
    client.post(
        "/runs/RUN-H/operations/register_mission",
        json={
            "command": {
                "mission_id": "MISSION-H",
                "station_name": "North",
                "people_count": 1,
                "created_at": "0",
            }
        },
    )

    state = client.get("/runs/RUN-H/state")
    assert state.json()["missions"][0]["mission_id"] == "MISSION-H"
    first = client.get("/runs/RUN-H/history").json()
    second = client.get("/runs/RUN-H/history").json()
    assert len(second) == len(first) + 1
    assert second[-1]["response"] == first


def test_untrusted_browser_origin_is_rejected():
    client = TestClient(create_app(allowed_origins=("http://localhost:3000",)))
    response = client.post(
        "/runs",
        headers={"Origin": "https://evil.example"},
        json={"application_run_id": "RUN-X", "central_id": "CENTRAL-X"},
    )
    assert response.status_code == 403
