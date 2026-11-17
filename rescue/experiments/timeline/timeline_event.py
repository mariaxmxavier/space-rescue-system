"""One scheduled scenario event with a normalized instant, kind and priority.

What: Defines TimelineEvent, the frozen value the timeline orders by instant and priority.
When called: Built whenever a scenario schedules an event on a run timeline.
Why: Validating and defaulting the fields once keeps heap ordering deterministic.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
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
class TimelineEvent:
    """A scenario event that a timeline can schedule.

    What: Holds instant, kind, scenario_sequence, payload and priority; priority None resolves to 0
      for expire events and 1 for the rest, and a blank kind is rejected.
    When called: Constructed by scenario code before Timeline.schedule.
    Why: Expirations must run before other events at the same instant.
    Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
    """

    instant: Instant
    kind: str
    scenario_sequence: int
    payload: object = None
    priority: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "instant", normalize_instant(self.instant))
        if not isinstance(self.kind, str) or not self.kind.strip():
            raise DomainValidationError("timeline event kind must be nonblank")
        object.__setattr__(
            self,
            "scenario_sequence",
            normalize_nonnegative_quantity(self.scenario_sequence),
        )
        priority = (
            (0 if self.kind == "expire" else 1)
            if self.priority is None
            else normalize_nonnegative_quantity(self.priority)
        )
        object.__setattr__(self, "priority", priority)
