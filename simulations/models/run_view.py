"""Typed projection of a created run."""

from typing import Annotated

from pydantic import Field

from simulations.models.base import StrictModel


class RunView(StrictModel):
    """Expose the real server run ID used by subsequent port calls."""

    run_id: Annotated[str, Field(min_length=1)]
