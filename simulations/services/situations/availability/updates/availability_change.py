"""Recipe for lowering B availability and making C temporarily unavailable."""

from simulations.models.evidence_predicate import EvidencePredicate
from simulations.models.fleet_update import FleetUpdate
from simulations.models.publish_fleet import PublishFleet
from simulations.models.situation_id import SituationId
from simulations.models.situation_recipe import SituationRecipe

RECIPE = SituationRecipe(
    situation_id=SituationId.AVAILABILITY_CHANGE,
    trigger="B availability matches its settled commitment and C becomes unavailable",
    action=PublishFleet(
        updates=(
            FleetUpdate(ship_key="B", capacity=2),
            FleetUpdate(ship_key="C", available=False),
        ),
    ),
    evidence=EvidencePredicate(check_name="confirmed", expected=6),
    dependencies=(SituationId.PARTIAL_AND_REFUSAL,),
)
