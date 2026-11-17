"""Tests for the RunSnapshot record.

What: Checks that a snapshot accepts only typed, deeply immutable run state.
When called: By pytest, in the unit suite for experiment models.
Why: A snapshot is stored and compared whole, so no part of it may change afterwards.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
"""

import pytest

from rescue.experiments.models import SimulationResult, SimulationRun
from rescue.experiments.models.run.run_snapshot import RunSnapshot
from rescue.market.models.b3_market import B3Market
from rescue.mission.models import MissionData
from rescue.mission.rules import register


def run():
    return SimulationRun(
        "RUN-1",
        "SCENARIO-1",
        1,
        "EARLIEST",
        1,
        0,
        10,
        "horizon_reached",
        SimulationResult(False, 0, 2, 1, 0),
    )


def mission():
    return register(MissionData("MISSION-1", "Station One", 2, 0))


def market():
    return B3Market("MARKET-1")


def snapshot(**changes):
    values = {"run": run(), "missions": (mission(),), "market": market()}
    values.update(changes)
    return RunSnapshot(**values)


def test_valid_snapshot_defaults_indexes_to_empty_tuples():
    value = snapshot()
    assert value.command_index == ()
    assert value.message_index == ()
    assert value.delivery_index == ()
    assert value.decision_index == ()


def test_missions_are_frozen_into_a_tuple():
    assert isinstance(snapshot(missions=[mission()]).missions, tuple)


def test_run_must_be_a_simulation_run():
    with pytest.raises(ValueError, match="requires a SimulationRun"):
        snapshot(run="RUN-1")


def test_missions_must_be_mission_values():
    with pytest.raises(ValueError, match="must be Mission values"):
        snapshot(missions=("MISSION-1",))


def test_market_must_be_a_b3_market():
    with pytest.raises(ValueError, match="requires a B3Market"):
        snapshot(market="MARKET-1")


def test_indexes_must_be_deeply_immutable():
    for name in ("command_index", "message_index", "delivery_index", "decision_index"):
        with pytest.raises(ValueError, match="deeply immutable"):
            snapshot(**{name: ([],)})


def test_valid_index_entries_are_kept():
    assert snapshot(command_index=(("A", 1),)).command_index == (("A", 1),)


def test_market_parts_must_be_deeply_immutable():
    with pytest.raises(ValueError, match="requires deeply immutable state"):
        snapshot(market=B3Market("MARKET-1", ships=([],)))
