"""Read-only typed projection of a message delivery attempt."""

from decimal import Decimal
from typing import Annotated

from pydantic import Field, field_validator

from simulations.models.base import StrictModel


class DeliveryView(StrictModel):
    """Expose message identity, session sequence and actual delivery disposition."""

    delivery_id: Annotated[str, Field(min_length=1)]
    message_id: Annotated[str, Field(min_length=1)]
    sequence: Annotated[int, Field(gt=0)]
    attempt_number: Annotated[int, Field(gt=0)]
    sent_at: Decimal
    received_at: Decimal | None = None
    disposition: Annotated[str, Field(min_length=1)]

    @field_validator("delivery_id", "message_id", "disposition")
    @classmethod
    def _nonblank(cls, value: str) -> str:
        """Reject blank identities and dispositions from delivery reads."""
        if not value.strip():
            raise ValueError("value must be nonblank")
        return value

    @field_validator("sent_at", "received_at")
    @classmethod
    def _valid_time(cls, value: Decimal | None) -> Decimal | None:
        """Keep delivery times exact, finite and nonnegative."""
        if value is not None and (not value.is_finite() or value < 0):
            raise ValueError("delivery time must be finite and nonnegative")
        return value
