"""Bounded, deterministically ordered event on one mission's virtual timeline."""

from decimal import Decimal
from typing import Annotated

from pydantic import Field, field_validator, model_validator

from simulations.models.base import StrictModel
from simulations.models.event_phase import EventPhase
from simulations.models.situation_id import SituationId
from simulations.models.timeline_action import TimelineAction


class TimelineEvent(StrictModel):
    """Pair a finite logical time and phase with one typed semantic action."""

    event_id: Annotated[str, Field(min_length=1)]
    time: Decimal
    phase: EventPhase
    ordinal: Annotated[int, Field(ge=0)]
    action: TimelineAction
    situation_ids: tuple[SituationId, ...] = ()

    @field_validator("event_id")
    @classmethod
    def _nonblank_id(cls, value: str) -> str:
        """Reject blank event identities."""
        if not value.strip():
            raise ValueError("event_id must be nonblank")
        return value

    @field_validator("time")
    @classmethod
    def _finite_nonnegative_time(cls, value: Decimal) -> Decimal:
        """Keep virtual time exact, finite and nonnegative."""
        if not value.is_finite() or value < 0:
            raise ValueError("time must be finite and nonnegative")
        return value

    @property
    def order_key(self) -> tuple[Decimal, EventPhase, int]:
        """Return the required stable heap ordering key."""
        return self.time, self.phase, self.ordinal

    @model_validator(mode="after")
    def _unique_situation_ids(self):
        """Keep one event from duplicating its own declared evidence identities."""
        if len(self.situation_ids) != len(set(self.situation_ids)):
            raise ValueError("event situation IDs must be unique")
        return self
