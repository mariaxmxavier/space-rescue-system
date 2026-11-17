"""Initial one-mission data for a composed simulation run."""

from typing import Annotated

from pydantic import Field, field_validator

from simulations.models.base import StrictModel


class MissionSetup(StrictModel):
    """Describe the mission created once when a scenario starts."""

    station_name: Annotated[str, Field(min_length=1)]
    demand: Annotated[int, Field(gt=0)]

    @field_validator("station_name")
    @classmethod
    def _nonblank_station(cls, value: str) -> str:
        """Reject station names that contain only whitespace."""
        if not value.strip():
            raise ValueError("station_name must be nonblank")
        return value
