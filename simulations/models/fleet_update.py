"""One symbolic ship change applied on the virtual timeline."""

from typing import Annotated

from pydantic import Field, model_validator

from simulations.models.base import StrictModel


class FleetUpdate(StrictModel):
    """Change offered capacity or availability for a previously registered ship."""

    ship_key: Annotated[str, Field(min_length=1)]
    capacity: Annotated[int, Field(ge=0)] | None = None
    available: bool | None = None
    offer_revision: Annotated[int, Field(gt=0)] | None = None

    @model_validator(mode="after")
    def _has_update(self):
        """Require a meaningful capacity, availability or offer revision change."""
        if self.capacity is None and self.available is None and self.offer_revision is None:
            raise ValueError("fleet update must change capacity, availability or offer revision")
        return self
