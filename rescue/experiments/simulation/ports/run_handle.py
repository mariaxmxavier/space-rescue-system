"""The parts of a started run that the simulation runner uses.

What: a Protocol with the run's `store`, `id_source` and `central`.
When called: returned by a `StartRun` factory; the runner reads `store.transact`,
  `store.snapshot`, `id_source.next_id` and the central's methods.
Why: the runner needs only these three members, so any run object that has them works and the
  runner never imports the bootstrap that builds it.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from __future__ import annotations

from typing import Protocol

from rescue.adapters.ports import IdSource, TransactionStore
from rescue.experiments.simulation.ports.simulation_central import SimulationCentral


class RunHandle(Protocol):
    """The parts of a started run that the simulation runner uses.

    What: the attributes `store`, `id_source` and `central`.
    When called: received from `StartRun` once per simulation.
    Why: it states what the runner needs from a run, without naming the concrete run context.
    Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
    """

    @property
    def store(self) -> TransactionStore: ...

    @property
    def id_source(self) -> IdSource: ...

    @property
    def central(self) -> SimulationCentral: ...
