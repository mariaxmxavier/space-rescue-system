"""Expected final accounting and evidence for one complete scenario run."""

from typing import Annotated

from pydantic import Field, field_validator

from simulations.models.base import StrictModel
from simulations.models.situation_id import SituationId


class FinalExpectation(StrictModel):
    """Declare final mission state independently from scenario pass or failure."""

    mission_status: Annotated[str, Field(min_length=1)]
    confirmed: Annotated[int, Field(ge=0)]
    pending: Annotated[int, Field(ge=0)]
    unconfirmed: Annotated[int, Field(ge=0)]
    required_situations: tuple[SituationId, ...]

    @field_validator("mission_status")
    @classmethod
    def _nonblank_status(cls, value: str) -> str:
        """Reject an empty API status expectation."""
        if not value.strip():
            raise ValueError("mission_status must be nonblank")
        return value
