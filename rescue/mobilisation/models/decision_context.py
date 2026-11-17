"""Decision context: the identity and time of a decision being made.

Transient value, not in the Mobilisation diagrams.
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import (
    DomainValidationError,
    Id,
    Instant,
    immutable_tuple,
    normalize_id,
    normalize_instant,
)


@dataclass(frozen=True, slots=True)
class DecisionContext:
    """The id, time and pre-assigned evaluation ids of one decision in progress.

    Supplied when a decision is requested so ids and time stay deterministic and the
    rules need no clock. Transient: it is not persisted and is not a Mobilisation diagram
    class.
    """

    decision_id: Id
    recorded_at: Instant
    evaluation_ids: tuple[Id, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", normalize_id(self.decision_id))
        object.__setattr__(self, "recorded_at", normalize_instant(self.recorded_at))
        evaluation_ids = immutable_tuple(self.evaluation_ids)
        for evaluation_id in evaluation_ids:
            normalize_id(evaluation_id)
        if len(evaluation_ids) != len(set(evaluation_ids)):
            raise DomainValidationError("evaluation IDs must be unique")
        object.__setattr__(self, "evaluation_ids", evaluation_ids)

    @property
    def time(self) -> Instant:
        """The instant the decision is recorded."""
        return self.recorded_at
