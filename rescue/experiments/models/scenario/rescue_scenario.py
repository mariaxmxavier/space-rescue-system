"""What: the full, bounded description of one experiment: baseline, scripted rules, horizon, seed and event budget.
When called: a simulation is configured to run.
Why: validating every reference and bound up front lets a run be replayed exactly.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.experiments.models._validation import finite_tuple
from rescue.experiments.models.scenario.communication_profile import CommunicationProfile
from rescue.experiments.models.scenario.run_baseline import RunBaseline
from rescue.experiments.models.scenario.scripted_response import ScriptedResponse
from rescue.market.models.availability import ShipAvailability
from rescue.values import (
    DomainValidationError,
    Instant,
    normalize_id,
    normalize_instant,
    normalize_positive_quantity,
)


@dataclass(frozen=True, slots=True)
class RescueScenario:
    """What: the full, bounded description of one experiment: baseline, scripted rules, horizon, seed and event budget.
    When called: a simulation is configured to run.
    Why: validating every reference and bound up front lets a run be replayed exactly.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
    """

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

        responses = finite_tuple(self.response_rules, "response_rules")
        changes = finite_tuple(self.availability_changes, "availability_changes")
        profiles = finite_tuple(self.communication_profiles, "communication_profiles")
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
