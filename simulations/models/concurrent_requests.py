"""Timeline action submitting a bounded group of competing requests."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from simulations.models.base import StrictModel
from simulations.models.selected_allocation import SelectedAllocation


class ConcurrentRequests(StrictModel):
    """Submit at most two copies of one selected allocation in one concurrent batch."""

    kind: Literal["concurrent_requests"] = "concurrent_requests"
    allocation: SelectedAllocation | None = None
    ship_key: str | None = None
    count: Annotated[int, Field(ge=2, le=2)] = 2

    @model_validator(mode="after")
    def _one_allocation_source(self):
        """Require either a real selected allocation or a symbolic runtime solver target."""
        if (self.allocation is None) == (self.ship_key is None):
            raise ValueError("specify exactly one allocation or symbolic ship_key")
        return self
