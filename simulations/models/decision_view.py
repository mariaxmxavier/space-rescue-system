"""Read-only typed projection of the solver decision and ranked evaluations."""

from typing import Annotated

from pydantic import Field

from simulations.models.base import StrictModel
from simulations.models.selected_allocation import SelectedAllocation


class DecisionView(StrictModel):
    """Expose selected solver evaluations in rank order for request submission."""

    decision_id: Annotated[str, Field(min_length=1)]
    allocations: tuple[SelectedAllocation, ...]
