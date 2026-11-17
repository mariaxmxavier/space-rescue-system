"""Exercise real HTTP simulations and their historical snapshots for the viewer."""

import pytest
from fastapi.testclient import TestClient

from rescue.api.app import create_app
from simulations.adapters.http.mission_api import HttpMissionApi
from simulations.entrypoints.viewer import catalogue, execute_case


@pytest.mark.parametrize(
    "case_id,count", [("baseline", 1), ("all10", 10), ("all11", 11), ("all12", 12)]
)
def test_profiles_have_real_evidence_and_preserved_snapshots(case_id, count):
    """Run each composed case and verify completion, evidence and seekable state."""
    with TestClient(create_app()) as client:
        result = execute_case(case_id, HttpMissionApi(client), f"test-{case_id}")
    assert result["result"]["passed"], result["result"]
    assert len(result["result"]["matched_situations"]) == count
    assert result["result"]["last_progress"]["confirmed"] == 10
    assert result["result"]["last_progress"]["pending"] == 0
    assert result["initial"]["progress"]["confirmed"] == 0
    assert result["initial"]["state"]["missions"][0]["requests"] == []
    assert result["frames"][-1]["progress"]["confirmed"] == 10
    assert len(result["frames"][-1]["state"]["missions"][0]["requests"]) >= 3
    times = [float(frame["logical_time"]) for frame in result["frames"]]
    assert times == sorted(times)
    assert len({frame["ordinal"] for frame in result["frames"]}) == len(times)


def test_catalogue_and_unknown_case_do_not_create_a_run():
    """Validate selection before any side effects and enumerate stable case IDs."""
    assert {item["id"] for item in catalogue()} == {
        "baseline",
        "all10",
        "all11",
        "all12",
        "multi-mission",
    }
    with TestClient(create_app()) as client:
        with pytest.raises(ValueError, match="Unknown"):
            execute_case("missing", HttpMissionApi(client), "unknown")
        assert client.get("/runs/unknown/state").status_code == 404


def test_all12_records_real_finality_ordering_and_capacity_competition():
    """Validate timeline probes independently of the summary's evidence booleans."""
    with TestClient(create_app()) as client:
        result = execute_case("all12", HttpMissionApi(client), "contract")
    frames = result["frames"]

    def at(time):
        return [item for item in frames if item["logical_time"] == str(time)]

    assert at(2)[-1]["progress"]["confirmed"] == 6
    assert at(2)[-1]["progress"]["pending"] == 0
    assert at(3)[-1]["progress"]["additional_needed"] == 4
    assert at(4)[-1]["progress"]["pending"] == 4
    assert at(5)[-1]["progress"]["pending"] == 2
    assert at(20)[-1]["progress"]["pending"] == 0
    assert at(21)[0]["outcomes"][0]["result"]["reason"] == "late"
    assert at(22)[0]["outcomes"][0]["result"]["reason"] == "duplicate_sequence"
    assert any(session["gaps"] for session in at(22)[0]["state"]["session_index"])
    competing = [
        item["result"]
        for item in at(23)[0]["outcomes"]
        if item["operation"] == "create_request"
        and item["input"]["command"]["ship_id"].endswith("-B")
    ]
    assert sorted(item["status"] for item in competing) == ["applied", "rejected"]
    assert (
        next(item for item in competing if item["status"] == "rejected")["reason"]
        == "insufficient_capacity"
    )
    assert at(23)[0]["progress"]["pending"] == 4
    assert at(24)[0]["outcomes"][0]["result"]["reason"] == "invalid_input"
    assert at(24)[0]["progress"] == at(23)[0]["progress"]
    assert at(26)[0]["progress"] == at(25)[-1]["progress"]
    replay = at(26)[0]["outcomes"][0]["input"]["command"]
    original = at(25)[0]["outcomes"][0]["input"]["command"]
    assert replay["message_id"] == original["message_id"]
    assert replay["envelope"] == original["envelope"]
    assert replay["delivery_id"] != original["delivery_id"]
    assert replay["attempt_number"] > original["attempt_number"]
