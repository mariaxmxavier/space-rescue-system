"""Summary of scenario expectations and observed outcomes."""

from typing import Annotated

from pydantic import Field

from simulations.models.base import StrictModel
from simulations.models.mission_progress import MissionProgress
from simulations.models.situation_id import SituationId


class ScenarioResult(StrictModel):
    """Report pass/fail and evidence independently from mission completion status."""

    profile_id: Annotated[str, Field(min_length=1)]
    run_id: Annotated[str, Field(min_length=1)]
    mission_id: Annotated[str, Field(min_length=1)]
    passed: bool
    matched_situations: tuple[SituationId, ...]
    missing_situations: tuple[SituationId, ...]
    last_progress: MissionProgress | None = None
    failure_detail: Annotated[str, Field(min_length=1)] | None = None
