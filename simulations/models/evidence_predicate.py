"""Typed expectation for one observable situation condition."""

from decimal import Decimal
from typing import Annotated, TypeAlias

from pydantic import Field

from simulations.models.base import StrictModel

EvidenceScalar: TypeAlias = str | int | bool | Decimal
EvidenceProjection: TypeAlias = EvidenceScalar | tuple[EvidenceScalar, ...]


class EvidencePredicate(StrictModel):
    """Declare a named projection and expected scalar values for recipe evidence."""

    check_name: Annotated[str, Field(min_length=1)]
    expected: EvidenceProjection
