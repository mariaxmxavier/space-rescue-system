"""Protect bounded immutable simulation inputs before any execution side effects."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from simulations.models.concurrent_requests import ConcurrentRequests
from simulations.models.mission_setup import MissionSetup
from simulations.models.observation import Observation
from simulations.models.operation_command import OperationCommand
from simulations.models.operation_name import OperationName
from simulations.models.operation_outcome import OperationOutcome
from simulations.models.policy_setup import PolicySetup
from simulations.models.reply_kind import ReplyKind
from simulations.models.request_selector import RequestSelector
from simulations.models.run_options import RunOptions
from simulations.models.scenario_profile import ScenarioProfile
from simulations.models.ship_reply import ShipReply
from simulations.models.solver_round import SolverRound
from simulations.services.scenarios.catalogue import profile


def test_scenario_is_frozen_and_rejects_boolean_demand_or_unknown_fields():
    """Prevent accidental mutations and type coercions from changing an accepted profile."""
    valid = profile("baseline")
    with pytest.raises(ValidationError):
        valid.scenario_id = "changed"
    with pytest.raises(ValidationError):
        MissionSetup(station_name="Aurora", demand=True)
    with pytest.raises(ValidationError):
        MissionSetup(station_name="Aurora", demand=1, unexpected="field")


@pytest.mark.parametrize(
    "changes",
    [
        {"scenario_id": " "},
        {"ships": ()},
        {"included_situations": (), "recipes": (), "event_budget": 1},
        {"horizon": Decimal("NaN")},
        {"horizon": Decimal("101")},
        {"horizon": Decimal("1")},
    ],
)
def test_profile_rejects_invalid_bounds_and_identity(changes):
    """Reject impossible execution bounds and empty identities during selection."""
    data = dict(profile("baseline"))
    data.update(changes)
    with pytest.raises(ValidationError):
        ScenarioProfile(**data)


def test_profile_rejects_duplicate_events_and_missing_recipes():
    """Make ordering unambiguous and ensure every declared situation has a recipe."""
    valid = profile("baseline")
    for changes in (
        {"events": (valid.events[0], valid.events[0])},
        {"ships": (valid.ships[0], valid.ships[0])},
        {"recipes": (valid.recipes[0], valid.recipes[0])},
        {"recipes": ()},
        {"included_situations": (*valid.included_situations, *valid.included_situations)},
    ):
        with pytest.raises(ValidationError):
            ScenarioProfile(**{**dict(valid), **changes})


@pytest.mark.parametrize("deadline", [Decimal("-1"), Decimal("Infinity"), Decimal("NaN")])
def test_solver_deadlines_must_be_finite_and_nonnegative(deadline):
    """Reject invalid logical times instead of letting them reach HTTP encoding."""
    with pytest.raises(ValidationError):
        SolverRound(response_deadline=deadline)


def test_concurrency_requires_one_real_or_symbolic_allocation_source():
    """Prevent an unbound batch or an ambiguous choice of allocation."""
    with pytest.raises(ValidationError):
        ConcurrentRequests()
    assert ConcurrentRequests(ship_key="B").count == 2


def test_observation_marks_unavailable_progress_and_rejects_invalid_time():
    """Keep missing observations distinct from zero and invalid timeline data."""
    outcome = OperationOutcome(operation=OperationName.GET_PROGRESS, http_status=200)
    base = {
        "ordinal": 0,
        "logical_time": Decimal("0"),
        "event_or_batch_id": "event",
        "outcome": outcome,
    }
    with pytest.raises(ValidationError):
        Observation(**base)
    assert Observation(**base, progress_unavailable=True).progress is None
    with pytest.raises(ValidationError):
        Observation(**{**base, "logical_time": Decimal("-1")}, progress_unavailable=True)


def test_command_rejects_missing_fields_and_invalid_time():
    """Keep operation-specific fields explicit rather than creating incomplete requests."""
    with pytest.raises(ValidationError):
        OperationCommand(operation=OperationName.CREATE_RUN)
    with pytest.raises(ValidationError):
        OperationCommand(operation=OperationName.CREATE_REQUEST)
    with pytest.raises(ValidationError):
        OperationCommand(
            operation=OperationName.GET_PROGRESS, mission_id="mission", at=Decimal("NaN")
        )


def test_reply_quantity_and_policy_labels_are_validated():
    """Require matching response quantities and usable policy and station identifiers."""
    selector = RequestSelector(ship_key="A", occurrence=1)
    with pytest.raises(ValidationError):
        ShipReply(request=selector, reply=ReplyKind.REFUSE, seats=1, message_label="bad")
    with pytest.raises(ValidationError):
        ShipReply(request=selector, reply=ReplyKind.CONFIRM, message_label="bad")
    with pytest.raises(ValidationError):
        ShipReply(
            request=selector, reply=ReplyKind.REFUSE, message_label="bad", sent_at=Decimal("-1")
        )
    with pytest.raises(ValidationError):
        PolicySetup(policy_id=" ")
    assert PolicySetup(policy_id="stable").policy_id == "stable"
    with pytest.raises(ValidationError):
        MissionSetup(station_name=" ", demand=1)


def test_runtime_options_require_unique_nonblank_selection_and_positive_timeouts():
    """Reject ambiguous profile lists or unusable connection budgets before network work."""
    assert RunOptions(base_url="http://localhost", profile_ids=("baseline",)).read_timeout == 10.0
    for changes in (
        {"base_url": " "},
        {"profile_ids": (" ",)},
        {"profile_ids": ("baseline", "baseline")},
        {"read_timeout": 0.0},
    ):
        with pytest.raises(ValidationError):
            RunOptions(**{"base_url": "http://localhost", "profile_ids": ("baseline",), **changes})
