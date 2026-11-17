"""Immutable scenario, baseline, run, and result values."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from rescue.market.models.availability import ShipAvailability
from rescue.market.models.b3_market import B3Market
from rescue.mission.models import Mission, RequestOutcome
from rescue.values import (
    DomainValidationError,
    Instant,
    normalize_id,
    normalize_instant,
    normalize_nonnegative_quantity,
    normalize_positive_quantity,
)


def _frozen_tree(value: object) -> bool:
    if value is None or type(value) in (str, int, bool, bytes) or isinstance(value, Decimal | Enum):
        return True
    if isinstance(value, tuple):
        return all(_frozen_tree(item) for item in value)
    from dataclasses import fields, is_dataclass

    if is_dataclass(value):
        params = getattr(type(value), "__dataclass_params__", None)
        return bool(params and params.frozen) and all(
            _frozen_tree(getattr(value, field.name)) for field in fields(value)
        )
    return False


def _finite_tuple(value: object, field_name: str) -> tuple:
    if not isinstance(value, (tuple, list)):
        raise DomainValidationError(f"{field_name} must be a finite tuple or list")
    return tuple(value)


@dataclass(frozen=True, slots=True)
class RunBaseline:
    """Value snapshot from which each independent simulation starts."""

    missions: tuple[Mission, ...]
    market: B3Market
    command_index: tuple[object, ...] = ()
    message_index: tuple[object, ...] = ()
    delivery_index: tuple[object, ...] = ()
    decision_index: tuple[object, ...] = ()
    session_index: tuple[object, ...] = ()

    def __post_init__(self) -> None:
        missions = _finite_tuple(self.missions, "baseline missions")
        if any(not isinstance(mission, Mission) for mission in missions):
            raise DomainValidationError("baseline missions must be Mission values")
        if len({mission.mission_id for mission in missions}) != len(missions):
            raise DomainValidationError("baseline mission IDs must be unique")
        if not isinstance(self.market, B3Market):
            raise DomainValidationError("baseline requires a B3Market value")
        object.__setattr__(self, "missions", missions)
        for name in (
            "command_index",
            "message_index",
            "delivery_index",
            "decision_index",
            "session_index",
        ):
            value = _finite_tuple(getattr(self, name), f"baseline {name}")
            if not _frozen_tree(value):
                raise DomainValidationError(f"baseline {name} must contain immutable values")
            object.__setattr__(self, name, value)
        if not _frozen_tree((missions, self.market)):
            raise DomainValidationError("baseline values must be deeply immutable")


@dataclass(frozen=True, slots=True)
class ScriptedResponse:
    """One finite response rule for a ship's one-based request ordinal."""

    ship_id: str
    request_ordinal: int
    outcome: str
    confirmed_seats: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "ship_id", normalize_id(self.ship_id))
        object.__setattr__(
            self, "request_ordinal", normalize_positive_quantity(self.request_ordinal)
        )
        if self.outcome not in {
            RequestOutcome.ACCEPTED,
            RequestOutcome.PARTIALLY_ACCEPTED,
            RequestOutcome.REFUSED,
        }:
            raise DomainValidationError("scripted response has an unsupported outcome")
        if self.confirmed_seats is not None:
            object.__setattr__(
                self,
                "confirmed_seats",
                normalize_nonnegative_quantity(self.confirmed_seats),
            )
        if self.outcome == RequestOutcome.REFUSED and self.confirmed_seats not in (None, 0):
            raise DomainValidationError("refused scripted responses cannot confirm seats")
        if self.outcome == RequestOutcome.PARTIALLY_ACCEPTED and self.confirmed_seats == 0:
            raise DomainValidationError("partial scripted responses require confirmed seats")


@dataclass(frozen=True, slots=True)
class CommunicationProfile:
    """Finite communication scripts for one ship; reordering changes equal-time priority."""

    profile_id: str
    ship_id: str
    outbound_delay_seconds: Instant
    decision_delay_seconds: Instant
    return_delay_seconds: Instant
    loss_rule: tuple[int, ...] = ()
    duplication_rule: tuple[int, ...] = ()
    reordering_rule: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", normalize_id(self.profile_id))
        object.__setattr__(self, "ship_id", normalize_id(self.ship_id))
        for name in (
            "outbound_delay_seconds",
            "decision_delay_seconds",
            "return_delay_seconds",
        ):
            object.__setattr__(self, name, normalize_instant(getattr(self, name)))
        for name in ("loss_rule", "duplication_rule", "reordering_rule"):
            values = _finite_tuple(getattr(self, name), name)
            if any(type(value) is not int or value <= 0 for value in values):
                raise DomainValidationError(f"{name} must contain positive request ordinals")
            if len(values) != len(set(values)):
                raise DomainValidationError(f"{name} request ordinals must be unique")
            object.__setattr__(self, name, values)
        lost = set(self.loss_rule)
        if lost.intersection(self.duplication_rule) or lost.intersection(self.reordering_rule):
            raise DomainValidationError(
                "lost response ordinals cannot also be duplicated or reordered"
            )


@dataclass(frozen=True, slots=True)
class RescueScenario:
    scenario_id: str
    revision: int
    name: str
    baseline: RunBaseline
    response_rules: tuple[ScriptedResponse, ...]
    availability_changes: tuple[ShipAvailability, ...]
    time_horizon_seconds: Instant
    seed: int
    event_budget: int
    communication_profiles: tuple[CommunicationProfile, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenario_id", normalize_id(self.scenario_id))
        object.__setattr__(self, "revision", normalize_positive_quantity(self.revision))
        if not isinstance(self.name, str) or not self.name.strip():
            raise DomainValidationError("scenario name must be nonblank")
        if not isinstance(self.baseline, RunBaseline):
            raise DomainValidationError("scenario requires a RunBaseline")
        horizon = normalize_instant(self.time_horizon_seconds)
        if horizon <= 0:
            raise DomainValidationError("scenario horizon must be positive")
        object.__setattr__(self, "time_horizon_seconds", horizon)
        if type(self.seed) is not int or self.seed < 0:
            raise DomainValidationError("scenario seed must be a nonnegative integer")
        object.__setattr__(self, "event_budget", normalize_positive_quantity(self.event_budget))

        responses = _finite_tuple(self.response_rules, "response_rules")
        changes = _finite_tuple(self.availability_changes, "availability_changes")
        profiles = _finite_tuple(self.communication_profiles, "communication_profiles")
        if any(not isinstance(rule, ScriptedResponse) for rule in responses):
            raise DomainValidationError("response_rules must contain ScriptedResponse values")
        if any(not isinstance(change, ShipAvailability) for change in changes):
            raise DomainValidationError("availability_changes must be ShipAvailability values")
        if any(not isinstance(profile, CommunicationProfile) for profile in profiles):
            raise DomainValidationError(
                "communication_profiles must contain CommunicationProfile values"
            )
        ship_ids = {ship.ship_id for ship in self.baseline.market.ships}
        if any(rule.ship_id not in ship_ids for rule in responses):
            raise DomainValidationError("response rule references an unknown baseline ship")
        if any(change.ship_id not in ship_ids for change in changes):
            raise DomainValidationError("availability change references an unknown baseline ship")
        if any(profile.ship_id not in ship_ids for profile in profiles):
            raise DomainValidationError("communication profile references an unknown baseline ship")
        response_keys = tuple((rule.ship_id, rule.request_ordinal) for rule in responses)
        if len(response_keys) != len(set(response_keys)):
            raise DomainValidationError("a ship request ordinal can have only one response rule")
        profile_ids = tuple(profile.profile_id for profile in profiles)
        profile_ships = tuple(profile.ship_id for profile in profiles)
        if len(profile_ids) != len(set(profile_ids)) or len(profile_ships) != len(
            set(profile_ships)
        ):
            raise DomainValidationError("communication profiles must have unique IDs and ships")
        availability_keys = tuple((change.ship_id, change.recorded_at) for change in changes)
        if len(availability_keys) != len(set(availability_keys)):
            raise DomainValidationError("a ship cannot have duplicate scenario availability times")
        object.__setattr__(self, "response_rules", responses)
        object.__setattr__(self, "availability_changes", changes)
        object.__setattr__(self, "communication_profiles", profiles)


@dataclass(frozen=True, slots=True)
class SimulationResult:
    completed: bool
    confirmed_seats: int
    unmet_demand: int
    requests_sent: int
    released_seats: int
    confirmation_elapsed_seconds: Instant | None = None
    latest_arrival_estimate_seconds: Instant | None = None

    def __post_init__(self) -> None:
        if type(self.completed) is not bool:
            raise DomainValidationError("completed must be boolean")
        for name in ("confirmed_seats", "unmet_demand", "requests_sent", "released_seats"):
            object.__setattr__(self, name, normalize_nonnegative_quantity(getattr(self, name)))
        for name in ("confirmation_elapsed_seconds", "latest_arrival_estimate_seconds"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, normalize_instant(value))
        if self.completed:
            if self.unmet_demand != 0 or self.confirmation_elapsed_seconds is None:
                raise DomainValidationError(
                    "completed results require zero unmet demand and a completion time"
                )
        elif self.confirmation_elapsed_seconds is not None:
            raise DomainValidationError("incomplete results cannot have a completion time")


@dataclass(frozen=True, slots=True)
class SimulationRun:
    run_id: str
    scenario_id: str
    scenario_revision: int
    policy_id: str
    policy_revision: int
    started_at: Instant
    finished_at: Instant | None
    status: str
    result: SimulationResult | None

    def __post_init__(self) -> None:
        for name in ("run_id", "scenario_id", "policy_id"):
            object.__setattr__(self, name, normalize_id(getattr(self, name)))
        object.__setattr__(
            self, "scenario_revision", normalize_positive_quantity(self.scenario_revision)
        )
        object.__setattr__(
            self, "policy_revision", normalize_positive_quantity(self.policy_revision)
        )
        started_at = normalize_instant(self.started_at)
        finished_at = None if self.finished_at is None else normalize_instant(self.finished_at)
        if finished_at is not None and finished_at < started_at:
            raise DomainValidationError("run cannot finish before it starts")
        if self.status not in {"running", "completed", "horizon_reached"}:
            raise DomainValidationError("unknown simulation status")
        if self.status == "running" and (finished_at is not None or self.result is not None):
            raise DomainValidationError("running simulations cannot have finish time or result")
        if self.status != "running" and finished_at is None:
            raise DomainValidationError("stopped simulations require a finish time")
        if self.result is not None and not isinstance(self.result, SimulationResult):
            raise DomainValidationError("run result must be a SimulationResult or None")
        if self.status == "completed" and self.result is not None and not self.result.completed:
            raise DomainValidationError("completed run requires a completed result")
        if self.status == "horizon_reached" and self.result is not None and self.result.completed:
            raise DomainValidationError("horizon-reached run cannot have a completed result")
        object.__setattr__(self, "started_at", started_at)
        object.__setattr__(self, "finished_at", finished_at)


@dataclass(frozen=True, slots=True)
class RunSnapshot:
    run: SimulationRun
    missions: tuple[Mission, ...]
    market: B3Market
    command_index: tuple[object, ...] = ()
    message_index: tuple[object, ...] = ()
    delivery_index: tuple[object, ...] = ()
    decision_index: tuple[object, ...] = ()
    session_index: tuple[object, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.run, SimulationRun):
            raise DomainValidationError("snapshot requires a SimulationRun")
        missions = _finite_tuple(self.missions, "snapshot missions")
        if any(not isinstance(mission, Mission) for mission in missions):
            raise DomainValidationError("snapshot missions must be Mission values")
        if not isinstance(self.market, B3Market):
            raise DomainValidationError("snapshot requires a B3Market")
        object.__setattr__(self, "missions", missions)
        for name in (
            "command_index",
            "message_index",
            "delivery_index",
            "decision_index",
            "session_index",
        ):
            value = _finite_tuple(getattr(self, name), f"snapshot {name}")
            if not _frozen_tree(value):
                raise DomainValidationError(f"snapshot {name} must be deeply immutable")
            object.__setattr__(self, name, value)
        if not _frozen_tree((missions, self.market)):
            raise DomainValidationError("snapshot requires deeply immutable state")
