"""Tests for the SimulationRun record.

What: Checks the identity, revision, time and status rules of one simulation run.
When called: By pytest, in the unit suite for experiment models.
Why: A stored run must have a consistent status, finish time and result.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
"""

from decimal import Decimal

import pytest

from rescue.experiments.models import SimulationResult
from rescue.experiments.models.run.simulation_run import SimulationRun


def result(completed=False):
    if completed:
        return SimulationResult(True, 2, 0, 1, 0, confirmation_elapsed_seconds=4)
    return SimulationResult(False, 1, 1, 1, 0)


def run(**changes):
    values = {
        "run_id": "RUN-1",
        "scenario_id": "SCENARIO-1",
        "scenario_revision": 1,
        "policy_id": "EARLIEST",
        "policy_revision": 1,
        "started_at": 0,
        "finished_at": 10,
        "status": "horizon_reached",
        "result": result(),
    }
    values.update(changes)
    return SimulationRun(**values)


def test_valid_run_normalises_times():
    value = run()
    assert value.started_at == Decimal(0)
    assert value.finished_at == Decimal(10)


def test_running_run_has_no_finish_time_or_result():
    value = run(status="running", finished_at=None, result=None)
    assert value.finished_at is None
    with pytest.raises(ValueError, match="running simulations cannot"):
        run(status="running", finished_at=None)
    with pytest.raises(ValueError, match="running simulations cannot"):
        run(status="running", result=None)


def test_stopped_run_requires_a_finish_time():
    with pytest.raises(ValueError, match="stopped simulations require"):
        run(finished_at=None)


def test_run_cannot_finish_before_it_starts():
    with pytest.raises(ValueError, match="cannot finish before"):
        run(started_at=5, finished_at=4)


def test_unknown_status_is_rejected():
    with pytest.raises(ValueError, match="unknown simulation status"):
        run(status="paused")


def test_result_must_be_a_simulation_result():
    with pytest.raises(ValueError, match="SimulationResult or None"):
        run(result="done")


def test_status_and_result_completion_must_agree():
    with pytest.raises(ValueError, match="completed run requires"):
        run(status="completed", result=result(completed=False))
    with pytest.raises(ValueError, match="horizon-reached run cannot"):
        run(status="horizon_reached", result=result(completed=True))
    assert run(status="completed", result=result(completed=True)).status == "completed"


def test_ids_and_revisions_are_validated():
    with pytest.raises(ValueError):
        run(run_id="")
    with pytest.raises(ValueError):
        run(scenario_revision=0)
    with pytest.raises(ValueError):
        run(policy_revision=0)
