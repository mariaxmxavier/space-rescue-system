"""What: the value snapshot each independent simulation starts from.
When called: built once per scenario, and validated when constructed.
Why: every run starts from identical missions and market, so comparisons are fair.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.experiments.models._validation import finite_tuple, frozen_tree
from rescue.market.models.b3_market import B3Market
from rescue.mission.models import Mission
from rescue.values import DomainValidationError


@dataclass(frozen=True, slots=True)
class RunBaseline:
    """What: the value snapshot each independent simulation starts from.
    When called: built once per scenario, and validated when constructed.
    Why: every run starts from identical missions and market, so comparisons are fair.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
    """

    missions: tuple[Mission, ...]
    market: B3Market
    command_index: tuple[object, ...] = ()
    message_index: tuple[object, ...] = ()
    delivery_index: tuple[object, ...] = ()
    decision_index: tuple[object, ...] = ()

    def __post_init__(self) -> None:
        missions = finite_tuple(self.missions, "baseline missions")
        if any(not isinstance(mission, Mission) for mission in missions):
            raise DomainValidationError("baseline missions must be Mission values")
        if len({mission.mission_id for mission in missions}) != len(missions):
            raise DomainValidationError("baseline mission IDs must be unique")
        if not isinstance(self.market, B3Market):
            raise DomainValidationError("baseline requires a B3Market value")
        object.__setattr__(self, "missions", missions)
        for name in (
            "command_index",
            "message_index",
            "delivery_index",
            "decision_index",
        ):
            value = finite_tuple(getattr(self, name), f"baseline {name}")
            if not frozen_tree(value):
                raise DomainValidationError(f"baseline {name} must contain immutable values")
            object.__setattr__(self, name, value)
        if not frozen_tree((missions, self.market)):
            raise DomainValidationError("baseline values must be deeply immutable")
