"""Timeline action requesting an explicit read-only observation."""

from typing import Annotated, Literal

from pydantic import Field

from simulations.models.base import StrictModel


class Observe(StrictModel):
    """Read authoritative progress or request/session details after an event."""

    kind: Literal["observe"] = "observe"
    reason: Annotated[str, Field(min_length=1)]
