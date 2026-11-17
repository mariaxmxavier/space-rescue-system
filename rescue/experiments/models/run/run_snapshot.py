"""RunSnapshot: the whole stored state of one run.

What: Holds the run, its missions, its market and the four command, message, delivery and
  decision indexes.
When called: Built when a run is saved or compared.
Why: Rejects any state that could change after capture, so stored runs stay comparable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.experiments.models._validation import finite_tuple, frozen_tree
from rescue.experiments.models.run.simulation_run import SimulationRun
from rescue.market.models.b3_market import B3Market
from rescue.mission.models import Mission
from rescue.values import DomainValidationError


@dataclass(frozen=True, slots=True)
class RunSnapshot:
    """The whole stored state of one run.

    What: Holds the run, its missions, its market and the four indexes.
    When called: Built when a run is saved or compared.
    Why: Every part must be deeply immutable so a stored run cannot drift.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
    """

    run: SimulationRun
    missions: tuple[Mission, ...]
    market: B3Market
    command_index: tuple[object, ...] = ()
    message_index: tuple[object, ...] = ()
    delivery_index: tuple[object, ...] = ()
    decision_index: tuple[object, ...] = ()
    session_index: tuple[object, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.run, SimulationRun):
            raise DomainValidationError("snapshot requires a SimulationRun")
        missions = finite_tuple(self.missions, "snapshot missions")
        if any(not isinstance(mission, Mission) for mission in missions):
            raise DomainValidationError("snapshot missions must be Mission values")
        if not isinstance(self.market, B3Market):
            raise DomainValidationError("snapshot requires a B3Market")
        object.__setattr__(self, "missions", missions)
        for name in (
            "command_index",
            "message_index",
            "delivery_index",
            "decision_index",
            "session_index",
        ):
            value = finite_tuple(getattr(self, name), f"snapshot {name}")
            if not frozen_tree(value):
                raise DomainValidationError(f"snapshot {name} must be deeply immutable")
            object.__setattr__(self, name, value)
        if not frozen_tree((missions, self.market)):
            raise DomainValidationError("snapshot requires deeply immutable state")
