"""Reusable semantic recipe and evidence declaration for one situation."""

from typing import Annotated

from pydantic import Field

from simulations.models.base import StrictModel
from simulations.models.evidence_predicate import EvidencePredicate
from simulations.models.situation_id import SituationId
from simulations.models.timeline_action import TimelineAction


class SituationRecipe(StrictModel):
    """Describe a situation trigger, typed action, proof and optional prerequisites."""

    situation_id: SituationId
    trigger: Annotated[str, Field(min_length=1)]
    action: TimelineAction
    evidence: EvidencePredicate
    dependencies: tuple[SituationId, ...] = ()
