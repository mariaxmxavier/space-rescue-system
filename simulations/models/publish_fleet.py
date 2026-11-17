"""Timeline action that publishes one or more fleet changes."""

from typing import Annotated, Literal

from pydantic import Field, field_validator

from simulations.models.base import StrictModel
from simulations.models.fleet_update import FleetUpdate


class PublishFleet(StrictModel):
    """Schedule availability and offer changes without coupling recipes to HTTP."""

    kind: Literal["publish_fleet"] = "publish_fleet"
    updates: Annotated[tuple[FleetUpdate, ...], Field(min_length=1)]

    @field_validator("updates")
    @classmethod
    def _unique_ship_keys(cls, updates: tuple[FleetUpdate, ...]) -> tuple[FleetUpdate, ...]:
        """Require a batch to change each ship at most once."""
        keys = tuple(update.ship_key for update in updates)
        if len(keys) != len(set(keys)):
            raise ValueError("fleet update ship keys must be unique")
        return updates
