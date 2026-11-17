"""Timeline action that delivers a ship response for a symbolic request."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, model_validator

from simulations.models.base import StrictModel
from simulations.models.reply_kind import ReplyKind
from simulations.models.request_selector import RequestSelector


class ShipReply(StrictModel):
    """Describe a response quantity while leaving message and request IDs to runtime binding."""

    kind: Literal["ship_reply"] = "ship_reply"
    request: RequestSelector
    reply: ReplyKind
    seats: Annotated[int, Field(ge=0)] | None = None
    message_label: Annotated[str, Field(min_length=1)]
    delivery_attempt: Annotated[int, Field(gt=0)] = 1
    sent_at: Decimal | None = None
    replay_of: Annotated[str, Field(min_length=1)] | None = None
    sequence: Annotated[int, Field(gt=0)] | None = None

    @model_validator(mode="after")
    def _quantity_matches_reply(self):
        """Require quantities for confirm/partial responses and omit them for refusal."""
        if self.reply is ReplyKind.REFUSE and self.seats is not None:
            raise ValueError("refusal cannot specify seats")
        if self.reply is not ReplyKind.REFUSE and self.seats is None:
            raise ValueError("confirmation must specify seats")
        if self.sent_at is not None and (not self.sent_at.is_finite() or self.sent_at < 0):
            raise ValueError("sent_at must be finite and nonnegative")
        return self
