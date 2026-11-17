"""Named server identifier included in an operation result."""

from typing import Annotated

from pydantic import Field

from simulations.models.base import StrictModel


class Identifier(StrictModel):
    """Carry a typed key/value identity pair without an unstructured mapping."""

    name: Annotated[str, Field(min_length=1)]
    value: Annotated[str, Field(min_length=1)]
