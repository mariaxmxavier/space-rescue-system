"""Typed HTTP and application result for one operation or read."""

from typing import Annotated, TypeAlias

from pydantic import Field

from simulations.models.api_state import ApiState
from simulations.models.base import StrictModel
from simulations.models.decision_view import DecisionView
from simulations.models.delivery_view import DeliveryView
from simulations.models.identifier import Identifier
from simulations.models.mission_progress import MissionProgress
from simulations.models.operation_name import OperationName
from simulations.models.request_view import RequestView
from simulations.models.run_view import RunView
from simulations.models.session_view import SessionView

OperationValue: TypeAlias = (
    RunView
    | DecisionView
    | MissionProgress
    | RequestView
    | SessionView
    | ApiState
    | tuple[DeliveryView, ...]
)


class OperationOutcome(StrictModel):
    """Keep HTTP failure separate from a normal business rejection response."""

    operation: OperationName
    http_status: Annotated[int, Field(ge=100, le=599)]
    application_status: Annotated[str, Field(min_length=1)] | None = None
    reason: Annotated[str, Field(min_length=1)] | None = None
    value: OperationValue | None = None
    identifiers: tuple[Identifier, ...] = ()
