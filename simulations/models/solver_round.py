"""Timeline action that obtains a fresh solver recommendation."""

from decimal import Decimal
from typing import Literal

from pydantic import field_validator

from simulations.models.base import StrictModel


class SolverRound(StrictModel):
    """Request a solver proposal and explicitly state whether selected work is submitted."""

    kind: Literal["solver_round"] = "solver_round"
    submit: bool = True
    response_deadline: Decimal

    @field_validator("response_deadline")
    @classmethod
    def _finite_deadline(cls, value: Decimal) -> Decimal:
        """Require a finite nonnegative deadline for requests created in the solver round."""
        if not value.is_finite() or value < 0:
            raise ValueError("response_deadline must be finite and nonnegative")
        return value
