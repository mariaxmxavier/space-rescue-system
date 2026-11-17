"""Verify that playback records the HTTP inputs and outputs used to prepare it."""

import pytest
from fastapi.testclient import TestClient

from rescue.api.app import create_app
from simulations.adapters.http.mission_api import HttpMissionApi
from simulations.entrypoints.viewer import execute_case


@pytest.mark.parametrize("case_id", ["all12", "multi-mission"])
def test_transcript_includes_setup_state_and_progress_calls(case_id):
    """Keep actual setup, state and progress exchanges alongside each snapshot."""
    with TestClient(create_app()) as client:
        transcript = execute_case(case_id, HttpMissionApi(client), f"technical-{case_id}")
    assert transcript["result"]["passed"]
    initial = transcript["initial"]["calls"]
    created = next(call for call in initial if call["operation"] == "create_run")
    assert created["input"]["application_run_id"] == transcript["run_id"]
    assert created["result"]["application_run_id"] == transcript["run_id"]
    state_read = next(call for call in initial if call["operation"] == "read_state")
    assert state_read["result"] == transcript["initial"]["state"]
    for frame in transcript["frames"]:
        progress_reads = [call for call in frame["calls"] if call["operation"] == "get_progress"]
        assert progress_reads
        assert all("input" in call and "result" in call for call in frame["calls"])
        assert all(call["input"]["now"] == frame["logical_time"] for call in progress_reads)
