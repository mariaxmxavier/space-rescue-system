"""Typed input envelope for one operation sent through the mission API port."""

from decimal import Decimal
from typing import Annotated

from pydantic import Field, model_validator

from simulations.models.base import StrictModel
from simulations.models.fleet_update import FleetUpdate
from simulations.models.mission_setup import MissionSetup
from simulations.models.operation_name import OperationName
from simulations.models.policy_setup import PolicySetup
from simulations.models.reply_kind import ReplyKind
from simulations.models.response_outcome import ResponseOutcome
from simulations.models.selected_allocation import SelectedAllocation
from simulations.models.session_envelope import SessionEnvelope
from simulations.models.ship_setup import ShipSetup


class OperationCommand(StrictModel):
    """Carry strictly typed operation data and validate its operation-specific shape."""

    operation: OperationName
    command_id: Annotated[str, Field(min_length=1)] | None = None
    mission: MissionSetup | None = None
    ship: ShipSetup | None = None
    fleet_update: FleetUpdate | None = None
    policy: PolicySetup | None = None
    allocation: SelectedAllocation | None = None
    mission_id: Annotated[str, Field(min_length=1)] | None = None
    ship_id: Annotated[str, Field(min_length=1)] | None = None
    availability_id: Annotated[str, Field(min_length=1)] | None = None
    offer_id: Annotated[str, Field(min_length=1)] | None = None
    revision_id: Annotated[str, Field(min_length=1)] | None = None
    revision_number: Annotated[int, Field(gt=0)] | None = None
    capacity: Annotated[int, Field(ge=0)] | None = None
    offer_capacity: Annotated[int, Field(gt=0)] | None = None
    arrival_estimate: Decimal | None = None
    available: bool | None = None
    policy_id: Annotated[str, Field(min_length=1)] | None = None
    policy_revision: Annotated[int, Field(gt=0)] | None = None
    request_id: Annotated[str, Field(min_length=1)] | None = None
    requested_seats: Annotated[int, Field(gt=0)] | None = None
    decision_id: Annotated[str, Field(min_length=1)] | None = None
    response_deadline: Decimal | None = None
    at: Decimal | None = None
    reply: ReplyKind | None = None
    seats: Annotated[int, Field(ge=0)] | None = None
    outcome: ResponseOutcome | None = None
    confirmed_seats: Annotated[int, Field(ge=0)] | None = None
    message_id: Annotated[str, Field(min_length=1)] | None = None
    delivery_id: Annotated[str, Field(min_length=1)] | None = None
    sequence: Annotated[int, Field(gt=0)] | None = None
    attempt_number: Annotated[int, Field(gt=0)] | None = None
    session_id: Annotated[str, Field(min_length=1)] | None = None
    envelope: SessionEnvelope | None = None
    sent_at: Decimal | None = None
    received_at: Decimal | None = None
    communication_rtt_seconds: Decimal | None = None
    reason: Annotated[str, Field(min_length=1)] | None = None
    limit: Annotated[int, Field(gt=0)] | None = None

    @model_validator(mode="after")
    def _validate_operation_contract(self):
        """Validate exact instants, envelope agreement and required operation inputs."""
        instants = (
            self.response_deadline,
            self.at,
            self.arrival_estimate,
            self.sent_at,
            self.received_at,
            self.communication_rtt_seconds,
        )
        if any(value is not None and (not value.is_finite() or value < 0) for value in instants):
            raise ValueError("operation times must be finite and nonnegative")
        if self.sequence is not None and self.envelope is not None:
            if self.sequence != self.envelope.sequence:
                raise ValueError("sequence must match the response envelope")

        required: dict[OperationName, tuple[str, ...]] = {
            OperationName.REGISTER_MISSION: ("mission_id", "mission", "at"),
            OperationName.REGISTER_SHIP: ("ship_id", "ship"),
            OperationName.PUBLISH_AVAILABILITY: (
                "availability_id",
                "ship_id",
                "capacity",
                "arrival_estimate",
                "available",
                "at",
            ),
            OperationName.PUBLISH_OFFER: (
                "offer_id",
                "mission_id",
                "ship_id",
                "revision_id",
                "revision_number",
                "offer_capacity",
                "arrival_estimate",
                "available",
                "at",
            ),
            OperationName.MOBILISE: ("mission_id", "policy_id", "policy_revision", "at"),
            OperationName.CREATE_REQUEST: (
                "command_id",
                "mission_id",
                "ship_id",
                "requested_seats",
                "revision_id",
                "at",
                "response_deadline",
            ),
            OperationName.RECORD_RESPONSE: (
                "request_id",
                "message_id",
                "delivery_id",
                "attempt_number",
                "outcome",
                "confirmed_seats",
                "sent_at",
                "envelope",
            ),
            OperationName.CANCEL_REQUEST: ("mission_id", "request_id", "at", "reason"),
            OperationName.EXPIRE_REQUEST: ("mission_id", "request_id", "at"),
            OperationName.GET_PROGRESS: ("mission_id", "at"),
            OperationName.GET_SESSION: ("session_id",),
            OperationName.GET_DELIVERIES: ("message_id",),
        }
        if self.operation is OperationName.CREATE_RUN:
            raise ValueError("run creation uses MissionApiABC.create_run")
        missing = tuple(name for name in required[self.operation] if getattr(self, name) is None)
        if missing:
            raise ValueError(
                f"{self.operation.value} is missing required fields: {', '.join(missing)}"
            )
        return self
