"""Recipe for observing a temporary demand shortfall with no free ships."""

from decimal import Decimal

from simulations.models.evidence_predicate import EvidencePredicate
from simulations.models.situation_id import SituationId
from simulations.models.situation_recipe import SituationRecipe
from simulations.models.solver_round import SolverRound

RECIPE = SituationRecipe(
    situation_id=SituationId.INSUFFICIENT_CAPACITY,
    trigger="The solver has no available allocation for four uncovered seats",
    action=SolverRound(submit=False, response_deadline=Decimal("20")),
    evidence=EvidencePredicate(check_name="additional_needed", expected=4),
    dependencies=(SituationId.AVAILABILITY_CHANGE, SituationId.PARTIAL_AND_REFUSAL),
)
