"""Immutable composition of all state owned by one application run.

What: the RunState value holding the market, missions, session index and the run's other indexes.
When called: by bootstrap when a run starts, and by every transaction that publishes a replacement state.
Why: one immutable value lets a transaction publish the whole run state atomically and keeps the adapters free of application imports.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.communication.models.sessions.communication_session import CommunicationSession
from rescue.market.models.b3_market import B3Market
from rescue.mission.models import Mission
from rescue.values import DomainValidationError, immutable_tuple, is_deeply_immutable, normalize_id


@dataclass(frozen=True, slots=True)
class RunState:
    """The whole state of one run as one immutable value.

    What: holds the market, the missions, the session index and the indexes of commands, messages, deliveries, decisions, policies, scenarios and completed runs.
    When called: created by bootstrap and by the transaction store; every transaction publishes a replacement.
    Why: one immutable value lets a transaction publish the state atomically; construction refuses duplicate mission or session ids.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/entity-relationship-diagram.mmd
    """

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
        """Validate the state and freeze its collections.

        What: normalises the ids, checks the value types and unique ids, and turns every collection into a deeply immutable tuple.
        When called: automatically on every RunState construction.
        Why: a state that is not deeply immutable could change inside a transaction.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/entity-relationship-diagram.mmd
        """

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
        if not is_deeply_immutable(self.market) or not is_deeply_immutable(self.missions):
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
            if not is_deeply_immutable(getattr(self, field_name)):
                raise DomainValidationError(f"{field_name} must contain deeply immutable values")

    def mission(self, mission_id: str) -> Mission | None:
        """Return the mission with the given id, or None.

        What: looks a mission up by its normalised id.
        When called: by the run state unit tests; no service reads it today.
        Why: gives one lookup instead of scanning the tuple at each call site.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/entity-relationship-diagram.mmd
        """

        normalized = normalize_id(mission_id)
        return next((item for item in self.missions if item.mission_id == normalized), None)
