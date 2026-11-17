"""Verify real simulation preparation through the browser-facing API boundary."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from rescue.api.app import create_app


def test_catalogue_and_unknown_case_do_not_create_runs():
    """List all bounded profiles and reject an unknown selection without side effects."""
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/simulations/cases")
        assert response.status_code == 200
        cases = response.json()["cases"]
        assert {"baseline", "all10", "all11", "all12", "multi-mission"} <= {
            case["id"] for case in cases
        }
        assert all(case["name"] and case["description"] for case in cases)
        assert client.post("/simulations/cases/missing/runs", json={}).status_code == 404


@pytest.mark.parametrize("case_id", ["baseline", "all10", "all11", "all12"])
def test_prepared_case_contains_authoritative_seekable_state(case_id):
    """Execute each real case and retain initial and per-event committed records."""
    with TestClient(create_app()) as client:
        response = client.post(f"/simulations/cases/{case_id}/runs", json={})
        assert response.status_code == 200, response.text
        transcript = response.json()
        assert transcript["result"]["passed"], transcript["result"]
        assert transcript["initial"]["logical_time"] == "0"
        assert transcript["initial"]["progress"]["confirmed"] == 0
        assert transcript["frames"]
        final = transcript["frames"][-1]
        assert final["progress"]["confirmed"] == 10
        assert final["progress"]["pending"] == 0
        assert len(transcript["result"]["matched_situations"]) == (
            1 if case_id == "baseline" else int(case_id[3:])
        )
        state = client.get(f"/runs/{transcript['run_id']}/state").json()
        assert final["state"] == state
        assert transcript["initial"]["state"] != final["state"]


def test_repeated_and_concurrent_case_selection_use_isolated_runs():
    """Prepare independently even when two visitors select the same profile together."""
    with TestClient(create_app()) as client:
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = tuple(
                pool.map(
                    lambda _: client.post("/simulations/cases/baseline/runs", json={}), range(2)
                )
            )
        assert all(response.status_code == 200 for response in responses)
        transcripts = [response.json() for response in responses]
        assert len({item["run_id"] for item in transcripts}) == 2
        assert all(item["result"]["passed"] for item in transcripts)


def test_simulation_mutation_preserves_origin_policy():
    """Disallow unapproved browser origins before creating an execution."""
    with TestClient(create_app()) as client:
        response = client.post(
            "/simulations/cases/baseline/runs", json={}, headers={"Origin": "https://example.com"}
        )
        assert response.status_code == 403
