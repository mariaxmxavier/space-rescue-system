"""Verify high-demand missions enter a real shared simulation over time."""

from fastapi.testclient import TestClient

from rescue.api.app import create_app
from simulations.adapters.http.mission_api import HttpMissionApi
from simulations.entrypoints.viewer import catalogue, execute_case


def test_multiple_missions_arrive_and_all_twelve_situations_are_observed():
    """Additional real missions enter chronologically and retain independent progress."""
    assert "multi-mission" in {item["id"] for item in catalogue()}
    with TestClient(create_app()) as client:
        transcript = execute_case("multi-mission", HttpMissionApi(client), "multi")
    assert transcript["result"]["passed"], transcript["result"]
    assert len(transcript["result"]["matched_situations"]) == 12
    frames = transcript["frames"]
    assert len(frames[-1]["mission_progress"]) >= 4
    assert sum(progress["demand"] for progress in frames[-1]["mission_progress"].values()) >= 300
    assert len(frames[0]["mission_progress"]) == 1
    times = [float(frame["logical_time"]) for frame in frames]
    assert times == sorted(times)
    assert len(frames[-1]["state"]["missions"]) >= 4
    assert sum(progress["confirmed"] for progress in frames[-1]["mission_progress"].values()) == 370
    assert all(progress["pending"] == 0 for progress in frames[-1]["mission_progress"].values())
    arrivals = [frame for frame in frames if "arrives: 120" in frame["label"]]
    assert [frame["logical_time"] for frame in arrivals] == ["2", "8", "16"]
    offers = frames[-1]["state"]["market"]["offers"]
    assert any(
        offer["mission_id"].endswith("surge-1") and offer["ship_id"].endswith("-A")
        for offer in offers
    )
