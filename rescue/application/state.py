"""Immutable composition of all state owned by one application run."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
from enum import Enum

from rescue.communication.models.sessions.communication_session import CommunicationSession
from rescue.market.models.b3_market import B3Market
from rescue.mission.models import Mission
from rescue.values import DomainValidationError, immutable_tuple, normalize_id


def _deeply_immutable(value: object) -> bool:
    if value is None or type(value) in (str, int, bool, bytes) or isinstance(value, Decimal | Enum):
        return True
    if isinstance(value, tuple):
        return all(_deeply_immutable(item) for item in value)
    if is_dataclass(value):
        parameters = getattr(type(value), "__dataclass_params__", None)
        return bool(parameters and parameters.frozen) and all(
            _deeply_immutable(getattr(value, field.name)) for field in fields(value)
        )
    return False


@dataclass(frozen=True, slots=True)
class RunState:
    application_run_id: str
    central_id: str
    market: B3Market
    missions: tuple[Mission, ...] = ()
    command_index: tuple[object, ...] = ()
    message_index: tuple[object, ...] = ()
    delivery_index: tuple[object, ...] = ()
    decision_index: tuple[object, ...] = ()
    policies: tuple[object, ...] = ()
    scenarios: tuple[object, ...] = ()
    completed_runs: tuple[object, ...] = ()
    session_index: tuple[CommunicationSession, ...] = ()

    def __post_init__(self) -> None:
        normalize_id(self.application_run_id)
        normalize_id(self.central_id)
        if not isinstance(self.market, B3Market):
            raise DomainValidationError("run state requires a B3Market value")
        missions = immutable_tuple(self.missions)
        if any(not isinstance(mission, Mission) for mission in missions):
            raise DomainValidationError("run missions must be Mission values")
        if len({mission.mission_id for mission in missions}) != len(missions):
            raise DomainValidationError("mission IDs must be unique within a run")
        object.__setattr__(self, "missions", missions)
        sessions = immutable_tuple(self.session_index)
        if any(not isinstance(session, CommunicationSession) for session in sessions):
            raise DomainValidationError("run sessions must be CommunicationSession values")
        if len({session.session_id for session in sessions}) != len(sessions):
            raise DomainValidationError("session IDs must be unique within a run")
        object.__setattr__(self, "session_index", sessions)
        for field_name in (
            "command_index",
            "message_index",
            "delivery_index",
            "decision_index",
            "policies",
            "scenarios",
            "completed_runs",
        ):
            object.__setattr__(self, field_name, immutable_tuple(getattr(self, field_name)))
        if not _deeply_immutable(self.market) or not _deeply_immutable(self.missions):
            raise DomainValidationError("run state requires deeply immutable domain values")
        for field_name in (
            "command_index",
            "message_index",
            "delivery_index",
            "decision_index",
            "policies",
            "scenarios",
            "completed_runs",
            "session_index",
        ):
            if not _deeply_immutable(getattr(self, field_name)):
                raise DomainValidationError(f"{field_name} must contain deeply immutable values")

    def mission(self, mission_id: str) -> Mission | None:
        normalized = normalize_id(mission_id)
        return next((item for item in self.missions if item.mission_id == normalized), None)
