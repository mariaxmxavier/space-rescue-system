"""Read-only typed projection of one request returned by the mission API."""

from decimal import Decimal
from typing import Annotated

from pydantic import Field, field_validator

from simulations.models.base import StrictModel


class RequestView(StrictModel):
    """Provide real request identities and state to selectors and evidence checks."""

    request_id: Annotated[str, Field(min_length=1)]
    mission_id: Annotated[str, Field(min_length=1)]
    ship_id: Annotated[str, Field(min_length=1)]
    requested_seats: Annotated[int, Field(gt=0)]
    confirmed_seats: Annotated[int, Field(ge=0)]
    status: Annotated[str, Field(min_length=1)]
    response_deadline: Decimal

    @field_validator("request_id", "mission_id", "ship_id", "status")
    @classmethod
    def _nonblank(cls, value: str) -> str:
        """Reject blank server values in a request projection."""
        if not value.strip():
            raise ValueError("value must be nonblank")
        return value

    @field_validator("response_deadline")
    @classmethod
    def _valid_deadline(cls, value: Decimal) -> Decimal:
        """Keep deadline precision and reject invalid logical instants."""
        if not value.is_finite() or value < 0:
            raise ValueError("response_deadline must be finite and nonnegative")
        return value
