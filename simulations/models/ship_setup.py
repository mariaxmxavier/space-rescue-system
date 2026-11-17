"""Initial ship capacity, identity and arrival data."""

from decimal import Decimal
from typing import Annotated

from pydantic import Field, field_validator

from simulations.models.base import StrictModel


class ShipSetup(StrictModel):
    """Describe one ship registered before the mission timeline begins."""

    ship_key: Annotated[str, Field(min_length=1)]
    name: Annotated[str, Field(min_length=1)]
    capacity: Annotated[int, Field(ge=0)]
    arrival: Decimal
    offer_revision: Annotated[int, Field(gt=0)]

    @field_validator("ship_key", "name")
    @classmethod
    def _nonblank(cls, value: str) -> str:
        """Reject identifiers that contain only whitespace."""
        if not value.strip():
            raise ValueError("value must be nonblank")
        return value

    @field_validator("arrival")
    @classmethod
    def _finite_nonnegative_arrival(cls, value: Decimal) -> Decimal:
        """Keep arrival estimates finite and nonnegative without float conversion."""
        if not value.is_finite() or value < 0:
            raise ValueError("arrival must be finite and nonnegative")
        return value
