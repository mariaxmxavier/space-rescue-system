"""Typed communication sequence identity sent with a response."""

from typing import Annotated

from pydantic import Field

from simulations.models.base import StrictModel
from simulations.models.session_direction import SessionDirection


class SessionEnvelope(StrictModel):
    """Carry the session, version, direction and explicit sequence of one message."""

    session_id: Annotated[str, Field(min_length=1)]
    version: Annotated[int, Field(gt=0)]
    direction: SessionDirection
    sequence: Annotated[int, Field(gt=0)]
