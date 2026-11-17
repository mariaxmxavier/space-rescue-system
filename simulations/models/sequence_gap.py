"""Typed server observation of an unapplied communication sequence range."""

from typing import Annotated

from pydantic import Field

from simulations.models.base import StrictModel


class SequenceGap(StrictModel):
    """Preserve the first missing sequence and count reported by the API."""

    from_sequence: Annotated[int, Field(gt=0)]
    count: Annotated[int, Field(gt=0)]
