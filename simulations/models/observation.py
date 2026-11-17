"""Immutable transcript observation after a timeline action or batch."""

from decimal import Decimal
from typing import Annotated

from pydantic import Field, model_validator

from simulations.models.base import StrictModel
from simulations.models.evidence import Evidence
from simulations.models.mission_progress import MissionProgress
from simulations.models.operation_outcome import OperationOutcome


class Observation(StrictModel):
    """Record the result, virtual time, progress availability and evidence at one step."""

    ordinal: Annotated[int, Field(ge=0)]
    logical_time: Decimal
    event_or_batch_id: Annotated[str, Field(min_length=1)]
    outcome: OperationOutcome
    progress: MissionProgress | None = None
    progress_unavailable: bool = False
    evidence: tuple[Evidence, ...] = ()

    @model_validator(mode="after")
    def _validate_progress_marker(self):
        """Require either a progress projection or its explicit unavailable marker."""
        if self.progress is None and not self.progress_unavailable:
            raise ValueError("missing progress must be marked unavailable")
        if self.progress is not None and self.progress_unavailable:
            raise ValueError("available progress cannot be marked unavailable")
        if not self.logical_time.is_finite() or self.logical_time < 0:
            raise ValueError("logical_time must be finite and nonnegative")
        return self
