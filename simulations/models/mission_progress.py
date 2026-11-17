"""Typed API progress projection for a single mission."""

from typing import Annotated

from pydantic import Field, model_validator

from simulations.models.base import StrictModel


class MissionProgress(StrictModel):
    """Expose authoritative mission seat accounting without modelling domain rules."""

    mission_id: Annotated[str, Field(min_length=1)]
    demand: Annotated[int, Field(gt=0)]
    confirmed: Annotated[int, Field(ge=0)]
    pending: Annotated[int, Field(ge=0)]
    unconfirmed: Annotated[int, Field(ge=0)]
    additional_needed: Annotated[int, Field(ge=0)]
    status: Annotated[str, Field(min_length=1)]

    @model_validator(mode="after")
    def _nonblank_ids_and_status(self):
        """Reject whitespace-only server identifiers and statuses."""
        if not self.mission_id.strip() or not self.status.strip():
            raise ValueError("mission_id and status must be nonblank")
        return self
