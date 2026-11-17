"""HTTP operation contract checks for feature 011."""

from fastapi.testclient import TestClient

from rescue.api.app import create_app


def test_create_run_and_return_complete_operation_results():
    client = TestClient(create_app())
    created = client.post(
        "/runs",
        json={"application_run_id": "RUN-HTTP", "central_id": "CENTRAL-HTTP"},
    )

    assert created.status_code == 201
    assert created.json() == {
        "application_run_id": "RUN-HTTP",
        "central_id": "CENTRAL-HTTP",
    }

    result = client.post(
        "/runs/RUN-HTTP/operations/register_mission",
        json={
            "command": {
                "mission_id": "MISSION-HTTP",
                "station_name": "North Station",
                "people_count": 3,
                "created_at": "0",
            }
        },
    )

    assert result.status_code == 200
    assert result.json()["status"] == "applied"
    assert result.json()["reason"] is None
    assert result.json()["value"]["mission_id"] == "MISSION-HTTP"
    assert result.json()["value"]["station_name"] == "North Station"
    assert result.json()["value"]["people_count"] == 3


def test_invalid_operation_input_is_reported_without_changing_run_state():
    client = TestClient(create_app())
    client.post(
        "/runs",
        json={"application_run_id": "RUN-INVALID", "central_id": "CENTRAL-INVALID"},
    )

    before = client.get("/runs/RUN-INVALID/state").json()
    rejected = client.post(
        "/runs/RUN-INVALID/operations/register_mission",
        json={"command": {"mission_id": "MISSION-BAD", "people_count": -1}},
    )
    after = client.get("/runs/RUN-INVALID/state").json()

    assert rejected.status_code == 400
    assert "detail" in rejected.json()
    assert after == before


def test_create_run_decodes_policy_for_mobilisation_operations():
    client = TestClient(create_app())
    created = client.post(
        "/runs",
        json={
            "application_run_id": "RUN-POLICY",
            "central_id": "CENTRAL-POLICY",
            "policies": [
                {
                    "policy_id": "POLICY-EARLY",
                    "revision": 1,
                    "name": "Earliest arrival",
                    "selection_criteria": "earliest_arrival",
                }
            ],
        },
    )

    assert created.status_code == 201
    state = client.get("/runs/RUN-POLICY/state").json()
    assert state["policies"][0]["policy_id"] == "POLICY-EARLY"
