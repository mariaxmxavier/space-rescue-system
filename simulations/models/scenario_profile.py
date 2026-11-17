"""Complete one-mission composition of setup, recipes, events and expectations."""

from decimal import Decimal
from typing import Annotated

from pydantic import Field, field_validator, model_validator

from simulations.models.base import StrictModel
from simulations.models.final_expectation import FinalExpectation
from simulations.models.mission_setup import MissionSetup
from simulations.models.policy_setup import PolicySetup
from simulations.models.ship_setup import ShipSetup
from simulations.models.situation_id import SituationId
from simulations.models.situation_recipe import SituationRecipe
from simulations.models.timeline_event import TimelineEvent


class ScenarioProfile(StrictModel):
    """Bundle one mission and its bounded reusable situation timeline."""

    scenario_id: Annotated[str, Field(min_length=1)]
    mission: MissionSetup
    ships: tuple[ShipSetup, ...]
    policy: PolicySetup = PolicySetup()
    included_situations: tuple[SituationId, ...]
    recipes: tuple[SituationRecipe, ...]
    events: tuple[TimelineEvent, ...] = ()
    expectation: FinalExpectation
    event_budget: Annotated[int, Field(gt=0, le=200)] = 200
    horizon: Decimal = Decimal("100")

    @field_validator("scenario_id")
    @classmethod
    def _nonblank_id(cls, value: str) -> str:
        """Reject blank profile identities."""
        if not value.strip():
            raise ValueError("scenario_id must be nonblank")
        return value

    @field_validator("ships")
    @classmethod
    def _unique_ships(cls, ships: tuple[ShipSetup, ...]) -> tuple[ShipSetup, ...]:
        """Require a nonempty fleet with unique symbolic ship keys."""
        keys = tuple(ship.ship_key for ship in ships)
        if not keys or len(keys) != len(set(keys)):
            raise ValueError("ships must be nonempty and ship keys unique")
        return ships

    @field_validator("included_situations")
    @classmethod
    def _unique_situations(cls, values: tuple[SituationId, ...]) -> tuple[SituationId, ...]:
        """Prevent a declared situation from being counted more than once."""
        if len(values) != len(set(values)):
            raise ValueError("included situations must be unique")
        return values

    @field_validator("horizon")
    @classmethod
    def _finite_horizon(cls, value: Decimal) -> Decimal:
        """Keep the configured time bound finite and within the supported horizon."""
        if not value.is_finite() or value < 0 or value > Decimal("100"):
            raise ValueError("horizon must be finite and between 0 and 100")
        return value

    @model_validator(mode="after")
    def _consistent_timeline(self):
        """Check recipe coverage and global event identities, ordinals and bounds."""
        recipes = tuple(recipe.situation_id for recipe in self.recipes)
        if len(recipes) != len(set(recipes)):
            raise ValueError("each situation may have only one recipe")
        if not set(self.included_situations).issubset(recipes):
            raise ValueError("every included situation must have a recipe")
        event_ids = tuple(event.event_id for event in self.events)
        ordinals = tuple(event.ordinal for event in self.events)
        if len(event_ids) != len(set(event_ids)) or len(ordinals) != len(set(ordinals)):
            raise ValueError("event IDs and ordinals must be unique")
        if len(self.events) > self.event_budget:
            raise ValueError("events exceed the event budget")
        if any(event.time > self.horizon for event in self.events):
            raise ValueError("event time exceeds the scenario horizon")
        return self
