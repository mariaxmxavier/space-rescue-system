"""Symbolic reference to an actual request returned by the API."""

from typing import Annotated

from pydantic import Field

from simulations.models.base import StrictModel


class RequestSelector(StrictModel):
    """Bind a ship and occurrence to a real request without predicting server IDs."""

    ship_key: Annotated[str, Field(min_length=1)]
    occurrence: Annotated[int, Field(gt=0)]
