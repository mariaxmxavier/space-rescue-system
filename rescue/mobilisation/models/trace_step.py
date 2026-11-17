"""Trace step: one recorded move of an allocator, kept for explanation and logging.

Transient value, not in the Mobilisation diagrams.
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.mobilisation.models.algorithm_name import AlgorithmName
from rescue.values import Id, immutable_tuple


@dataclass(frozen=True, slots=True)
class TraceStep:
    """A named step an allocator took, optionally about one ship, with string details.

    Emitted while an allocator runs and logged at DEBUG by the decision service, so a
    decision can be replayed from values alone.
    """

    algorithm: AlgorithmName
    step: str
    ship_id: Id | None
    detail: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        pairs = tuple((str(key), str(value)) for key, value in immutable_tuple(self.detail))
        object.__setattr__(self, "detail", pairs)
