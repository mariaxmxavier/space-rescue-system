"""Finish a simulation run.

What: builds the final `RunSnapshot` of a run, with its summarised result, from the store.
When called: once, after the timeline loop stops.
Why: the result is computed from the final state, so the run is built first without it and then
  replaced with the summarised copy.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from rescue.experiments.models import RescueScenario, RunSnapshot, SimulationRun
from rescue.experiments.results import summarize
from rescue.experiments.simulation.ports import RunHandle
from rescue.mobilisation.models import MobilisationPolicy


def finish_run(
    handle: RunHandle,
    scenario: RescueScenario,
    policy: MobilisationPolicy,
    run_id: str,
    started_at: Decimal,
    finished_at: Decimal,
    status: str,
) -> RunSnapshot:
    """Finish a simulation run.

    What: snapshots the store, builds a provisional run and snapshot, summarises it and returns
      the snapshot with the result attached to its run.
    When called: once per run, after the last event.
    Why: `summarize` needs a stopped snapshot, which exists only after the loop ends.
    Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
    """
    final_state = handle.store.snapshot()
    provisional_run = SimulationRun(
        run_id=run_id,
        scenario_id=scenario.scenario_id,
        scenario_revision=scenario.revision,
        policy_id=policy.policy_id,
        policy_revision=policy.revision,
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        result=None,
    )
    provisional_snapshot = RunSnapshot(
        run=provisional_run,
        missions=final_state.missions,
        market=final_state.market,
        command_index=final_state.command_index,
        message_index=final_state.message_index,
        delivery_index=final_state.delivery_index,
        decision_index=final_state.decision_index,
    )
    result = summarize(provisional_snapshot)
    finalized_run = replace(provisional_run, result=result)
    return replace(provisional_snapshot, run=finalized_run)
