"""Explicit runtime options supplied to a simulation entrypoint."""

from typing import Annotated

from pydantic import Field, field_validator

from simulations.models.base import StrictModel


class RunOptions(StrictModel):
    """Carry URL, profile selection and positive phase timeouts without environment reads."""

    base_url: Annotated[str, Field(min_length=1)]
    profile_ids: tuple[str, ...]
    connect_timeout: Annotated[float, Field(gt=0)] = 2.0
    pool_timeout: Annotated[float, Field(gt=0)] = 2.0
    read_timeout: Annotated[float, Field(gt=0)] = 10.0
    write_timeout: Annotated[float, Field(gt=0)] = 10.0

    @field_validator("base_url")
    @classmethod
    def _nonblank_base_url(cls, value: str) -> str:
        """Require an explicit endpoint instead of resolving environment state."""
        if not value.strip():
            raise ValueError("base_url must be nonblank")
        return value

    @field_validator("profile_ids")
    @classmethod
    def _nonblank_profiles(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        """Reject blank or duplicate profile selections."""
        if any(not value.strip() for value in values) or len(values) != len(set(values)):
            raise ValueError("profile IDs must be nonblank and unique")
        return values
