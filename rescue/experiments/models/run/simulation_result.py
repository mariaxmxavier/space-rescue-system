"""SimulationResult: the outcome figures of one finished run.

What: Holds completion, seat counts and the two optional time figures of a run.
When called: Built when a run stops, then stored inside its SimulationRun.
Why: Keeps the completion rules in one immutable value so a result cannot contradict itself.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import (
    DomainValidationError,
    Instant,
    normalize_instant,
    normalize_nonnegative_quantity,
)


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """The outcome figures of one finished run.

    What: Holds completion, seat counts and the two optional time figures of a run.
    When called: Built when a run stops, then stored inside its SimulationRun.
    Why: A completed result must have zero unmet demand and a completion time.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
    """

    completed: bool
    confirmed_seats: int
    unmet_demand: int
    requests_sent: int
    released_seats: int
    confirmation_elapsed_seconds: Instant | None = None
    latest_arrival_estimate_seconds: Instant | None = None

    def __post_init__(self) -> None:
        if type(self.completed) is not bool:
            raise DomainValidationError("completed must be boolean")
        for name in ("confirmed_seats", "unmet_demand", "requests_sent", "released_seats"):
            object.__setattr__(self, name, normalize_nonnegative_quantity(getattr(self, name)))
        for name in ("confirmation_elapsed_seconds", "latest_arrival_estimate_seconds"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, normalize_instant(value))
        if self.completed:
            if self.unmet_demand != 0 or self.confirmation_elapsed_seconds is None:
                raise DomainValidationError(
                    "completed results require zero unmet demand and a completion time"
                )
        elif self.confirmation_elapsed_seconds is not None:
            raise DomainValidationError("incomplete results cannot have a completion time")
