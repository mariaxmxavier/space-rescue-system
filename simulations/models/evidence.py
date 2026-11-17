"""Immutable evidence that a declared situation predicate was observed."""

from typing import Annotated

from pydantic import Field

from simulations.models.base import StrictModel
from simulations.models.evidence_predicate import EvidenceProjection
from simulations.models.situation_id import SituationId


class Evidence(StrictModel):
    """Record observed event IDs and typed expected/actual predicate projections."""

    situation_id: SituationId
    triggering_event_ids: tuple[str, ...]
    check_name: Annotated[str, Field(min_length=1)]
    expected: EvidenceProjection
    observed: EvidenceProjection
    matched: bool
