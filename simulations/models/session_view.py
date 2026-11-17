"""Read-only typed projection of one ship communication session."""

from typing import Annotated

from pydantic import Field, field_validator

from simulations.models.base import StrictModel
from simulations.models.sequence_gap import SequenceGap


class SessionView(StrictModel):
    """Expose sequence scope and gap information observed from the API."""

    session_id: Annotated[str, Field(min_length=1)]
    ship_id: Annotated[str, Field(min_length=1)] | None = None
    version: Annotated[int, Field(gt=0)]
    direction: Annotated[str, Field(min_length=1)] | None = None
    next_inbound: Annotated[int, Field(gt=0)]
    next_outbound: Annotated[int, Field(gt=0)]
    gaps: tuple[SequenceGap, ...] = ()

    @field_validator("session_id")
    @classmethod
    def _nonblank(cls, value: str) -> str:
        """Reject blank server values in a session projection."""
        if not value.strip():
            raise ValueError("value must be nonblank")
        return value

    @field_validator("ship_id", "direction")
    @classmethod
    def _nonblank_optional(cls, value: str | None) -> str | None:
        """Reject blank joined ship and direction values while allowing absent source fields."""
        if value is not None and not value.strip():
            raise ValueError("value must be nonblank")
        return value

    @property
    def missing_sequences(self) -> tuple[int, ...]:
        """Expand observed gap ranges for recipes that check one missing sequence."""
        return tuple(
            sequence
            for gap in self.gaps
            for sequence in range(gap.from_sequence, gap.from_sequence + gap.count)
        )
