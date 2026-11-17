"""Finite deterministic heap scheduler for simulated scenario events.

What: Defines Timeline, a run-local heap that orders TimelineEvent values and bounds their count.
When called: Created once per simulated run and drained by the run loop.
Why: One bounded, ordered queue makes every run reproducible and guarantees it terminates.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from __future__ import annotations

import heapq

from rescue.experiments.timeline.timeline_event import TimelineEvent
from rescue.values import (
    DomainValidationError,
    normalize_instant,
    normalize_positive_quantity,
)


class Timeline:
    """Run-local mutable heap whose scheduled event count is always bounded.

    What: Orders events by instant, priority, scenario_sequence and insertion order; peek_next and
      pop_next return None past the horizon; the event_budget + 1 th schedule raises
      DomainValidationError.
    When called: Constructed with a horizon and an event budget at the start of a run.
    Why: A finite, deterministic event order is what lets two runs of one scenario match exactly.
    Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
    """

    def __init__(self, horizon, event_budget: int) -> None:
        self.horizon = normalize_instant(horizon)
        if self.horizon <= 0:
            raise DomainValidationError("timeline horizon must be positive")
        self.event_budget = normalize_positive_quantity(event_budget)
        self._heap: list[tuple[object, ...]] = []
        self._insertion_sequence = 0
        self._scheduled_count = 0

    def schedule(self, event: TimelineEvent) -> None:
        if not isinstance(event, TimelineEvent):
            raise DomainValidationError("timeline accepts TimelineEvent values")
        if self._scheduled_count >= self.event_budget:
            raise DomainValidationError("scenario event budget exceeded")
        self._insertion_sequence += 1
        self._scheduled_count += 1
        heapq.heappush(
            self._heap,
            (
                event.instant,
                event.priority,
                event.scenario_sequence,
                self._insertion_sequence,
                event,
            ),
        )

    def peek_next(self) -> TimelineEvent | None:
        if not self._heap:
            return None
        instant, _, _, _, event = self._heap[0]
        return None if instant > self.horizon else event

    def pop_next(self) -> TimelineEvent | None:
        event = self.peek_next()
        if event is None:
            return None
        heapq.heappop(self._heap)
        return event

    @property
    def scheduled_count(self) -> int:
        return self._scheduled_count
