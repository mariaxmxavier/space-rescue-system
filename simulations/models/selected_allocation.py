"""Typed projection of one selected solver evaluation."""

from typing import Annotated

from pydantic import Field, field_validator

from simulations.models.base import StrictModel


class SelectedAllocation(StrictModel):
    """Carry a solver-selected ship quantity and its real decision revisions."""

    decision_id: Annotated[str, Field(min_length=1)]
    evaluation_id: Annotated[str, Field(min_length=1)]
    rank: Annotated[int, Field(gt=0)]
    ship_id: Annotated[str, Field(min_length=1)]
    proposed_seats: Annotated[int, Field(gt=0)]
    revision_id: Annotated[str, Field(min_length=1)]

    @field_validator("decision_id", "evaluation_id", "ship_id", "revision_id")
    @classmethod
    def _nonblank(cls, value: str) -> str:
        """Reject blank server identifiers in a solver projection."""
        if not value.strip():
            raise ValueError("identifier must be nonblank")
        return value
