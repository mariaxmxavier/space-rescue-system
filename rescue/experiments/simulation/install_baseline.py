"""Copy a baseline into a run's store.

What: `install_baseline` writes the baseline's market, missions and indexes into the run store.
When called: by the runner right after the run starts, before any event is scheduled.
Why: every run starts from the same immutable baseline under its own run id.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.experiments.models import RunBaseline
from rescue.experiments.simulation.ports import RunHandle


def _copy_command_index(entries: tuple[object, ...], run_id: str) -> tuple[object, ...]:
    """What: rewrites the run id of each five-item command entry.

    Why: baseline commands belong to the new run, so replays under it still match.
    """
    remapped = []
    for entry in entries:
        if isinstance(entry, tuple) and len(entry) == 5:
            remapped.append((run_id, *entry[1:]))
        else:
            remapped.append(entry)
    return tuple(remapped)


def install_baseline(handle: RunHandle, baseline: RunBaseline, run_id: str) -> None:
    """Copy a baseline into a run's store.

    What: replaces the store state's market, missions and four indexes with the baseline's,
      renaming the market and the command index to the run id.
    When called: once per run, right after the run starts.
    Why: each run begins from the same baseline without touching the source values.
    Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
    """

    def install(state):
        return (
            replace(
                state,
                market=replace(baseline.market, market_id=f"{run_id}-market"),
                missions=baseline.missions,
                command_index=_copy_command_index(baseline.command_index, run_id),
                message_index=baseline.message_index,
                delivery_index=baseline.delivery_index,
                decision_index=baseline.decision_index,
            ),
            None,
        )

    handle.store.transact(install)
