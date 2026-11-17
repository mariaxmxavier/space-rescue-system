"""Solver policy used for all mobilisation rounds in a simulation."""

from typing import Annotated

from pydantic import Field, field_validator

from simulations.models.base import StrictModel


class PolicySetup(StrictModel):
    """Declare the one deterministic policy registered for a scenario."""

    policy_id: Annotated[str, Field(min_length=1)] = "EARLIEST"
    policy_name: Annotated[str, Field(min_length=1)] = "EARLIEST"
    revision: Annotated[int, Field(gt=0)] = 1
    selection_criteria: Annotated[str, Field(min_length=1)] = "earliest_arrival"

    @field_validator("policy_id", "policy_name", "selection_criteria")
    @classmethod
    def _nonblank(cls, value: str) -> str:
        """Reject blank policy labels before they reach the API adapter."""
        if not value.strip():
            raise ValueError("value must be nonblank")
        return value
