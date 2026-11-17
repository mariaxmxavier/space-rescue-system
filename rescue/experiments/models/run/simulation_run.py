"""SimulationRun: the identity, timing, status and result of one run.

What: Holds which scenario and policy revision ran, when, its status and its result.
When called: Built when a run starts and rebuilt when it stops.
Why: Keeps status, finish time and result consistent in one immutable record.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.experiments.models.run.simulation_result import SimulationResult
from rescue.values import (
    DomainValidationError,
    Instant,
    normalize_id,
    normalize_instant,
    normalize_positive_quantity,
)


@dataclass(frozen=True, slots=True)
class SimulationRun:
    """The identity, timing, status and result of one run.

    What: Holds which scenario and policy revision ran, when, its status and its result.
    When called: Built when a run starts and rebuilt when it stops.
    Why: A running run has no finish time or result; a stopped run has a finish time.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
    """

    run_id: str
    scenario_id: str
    scenario_revision: int
    policy_id: str
    policy_revision: int
    started_at: Instant
    finished_at: Instant | None
    status: str
    result: SimulationResult | None

    def __post_init__(self) -> None:
        for name in ("run_id", "scenario_id", "policy_id"):
            object.__setattr__(self, name, normalize_id(getattr(self, name)))
        object.__setattr__(
            self, "scenario_revision", normalize_positive_quantity(self.scenario_revision)
        )
        object.__setattr__(
            self, "policy_revision", normalize_positive_quantity(self.policy_revision)
        )
        started_at = normalize_instant(self.started_at)
        finished_at = None if self.finished_at is None else normalize_instant(self.finished_at)
        if finished_at is not None and finished_at < started_at:
            raise DomainValidationError("run cannot finish before it starts")
        if self.status not in {"running", "completed", "horizon_reached"}:
            raise DomainValidationError("unknown simulation status")
        if self.status == "running" and (finished_at is not None or self.result is not None):
            raise DomainValidationError("running simulations cannot have finish time or result")
        if self.status != "running" and finished_at is None:
            raise DomainValidationError("stopped simulations require a finish time")
        if self.result is not None and not isinstance(self.result, SimulationResult):
            raise DomainValidationError("run result must be a SimulationResult or None")
        if self.status == "completed" and self.result is not None and not self.result.completed:
            raise DomainValidationError("completed run requires a completed result")
        if self.status == "horizon_reached" and self.result is not None and self.result.completed:
            raise DomainValidationError("horizon-reached run cannot have a completed result")
        object.__setattr__(self, "started_at", started_at)
        object.__setattr__(self, "finished_at", finished_at)
