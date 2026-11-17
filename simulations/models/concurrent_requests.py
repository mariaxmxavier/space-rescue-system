"""Timeline action submitting a bounded group of competing requests."""

from typing import Annotated, Literal

from pydantic import Field

from simulations.models.base import StrictModel
from simulations.models.selected_allocation import SelectedAllocation


class ConcurrentRequests(StrictModel):
    """Submit at most two copies of one selected allocation in one concurrent batch."""

    kind: Literal["concurrent_requests"] = "concurrent_requests"
    allocation: SelectedAllocation
    count: Annotated[int, Field(ge=2, le=2)] = 2
