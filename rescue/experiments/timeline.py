"""Finite deterministic heap scheduler for simulated scenario events."""

from __future__ import annotations

from dataclasses import dataclass
import heapq

from rescue.values import (
    DomainValidationError,
    Instant,
    normalize_instant,
    normalize_nonnegative_quantity,
    normalize_positive_quantity,
)


@dataclass(frozen=True, slots=True)
class TimelineEvent:
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
            0 if self.kind == "expire" else 1
        ) if self.priority is None else normalize_nonnegative_quantity(self.priority)
        object.__setattr__(self, "priority", priority)


class Timeline:
    """Run-local mutable heap whose scheduled event count is always bounded."""

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
