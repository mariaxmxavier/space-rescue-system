"""Tests for the apply_outcome rule: closing a seat request and rejecting every invalid answer."""

import copy

import pytest

from rescue.mission.models.mission.mission import Mission
from rescue.mission.models.mission.mission_data import MissionData
from rescue.mission.models.mission.seat_request import SeatRequest
from rescue.mission.models.vocabulary.history_action import HistoryAction
from rescue.mission.models.vocabulary.request_outcome import RequestOutcome
from rescue.mission.rules.add_request import add_request
from rescue.mission.rules.apply_outcome import apply_outcome
from rescue.mission.rules.progress import progress
from rescue.mission.rules.register import register
from rescue.values import DomainValidationError, TransitionContext

CLOSING_CASES = (
    ("accepted", 6),
    ("partially_accepted", 4),
    ("refused", 0),
    ("cancelled", 0),
    ("expired", 0),
)


def seat_request(**overrides):
    fields = {
        "request_id": "request-1",
        "command_id": "command-1",
        "mission_id": "mission-1",
        "ship_id": "ship-1",
        "requested_seats": 6,
        "confirmed_seats": 0,
        "outcome": RequestOutcome.PENDING,
        "submitted_at": 10,
        "response_deadline": 20,
    }
    return SeatRequest(**(fields | overrides))


def mission_with(*requests):
    return Mission(
        mission_id="mission-1",
        station_name="Station A",
        people_count=10,
        created_at=0,
        requests=requests,
    )


def context(at=12):
    return TransitionContext(event_id="outcome-1", at=at, reason="ship answered")


def closed_request():
    return seat_request(
        outcome=RequestOutcome.ACCEPTED,
        confirmed_seats=6,
        response_received_at=11,
        closed_at=11,
    )


def pending_mission(seats=6):
    mission = register(
        MissionData(
            mission_id="mission-1",
            station_name="Station A",
            people_count=10,
            created_at="0",
        )
    )
    request = SeatRequest(
        request_id="request-1",
        command_id="command-request-1",
        mission_id="mission-1",
        ship_id="ship-1",
        requested_seats=seats,
        confirmed_seats=0,
        outcome="pending",
        submitted_at="1",
        revision_id="revision-1",
    )
    return add_request(
        mission, request, TransitionContext(event_id="created", at="1", reason="test")
    )


def assert_closed(updated, outcome, confirmed):
    request = updated.requests[0]
    no_receipt = outcome in {"cancelled", "expired"}
    assert request.outcome is RequestOutcome(outcome)
    assert request.confirmed_seats == confirmed
    assert request.closed_at == 12
    assert request.response_received_at == (None if no_receipt else 12)
    assert len(updated.history) == 1
    assert updated.history[0].action is HistoryAction(outcome)
    assert updated.history[0].confirmed_seats_delta == confirmed
    assert updated.history[0].pending_seats_delta == -6


@pytest.mark.parametrize(("outcome", "confirmed"), CLOSING_CASES)
def test_string_outcome_closes_the_pending_request(outcome, confirmed):
    updated = apply_outcome(
        mission_with(seat_request()), "request-1", outcome, confirmed, context()
    )
    assert_closed(updated, outcome, confirmed)


@pytest.mark.parametrize(("outcome", "confirmed"), CLOSING_CASES)
def test_enum_outcome_closes_the_pending_request(outcome, confirmed):
    updated = apply_outcome(
        mission_with(seat_request()),
        "request-1",
        RequestOutcome(outcome),
        confirmed,
        context(),
    )
    assert_closed(updated, outcome, confirmed)


def test_only_the_named_request_changes_and_order_is_kept():
    first = seat_request(request_id="request-1", requested_seats=4)
    second = seat_request(request_id="request-2", requested_seats=6)
    updated = apply_outcome(mission_with(first, second), "request-2", "refused", 0, context())
    assert updated.requests[0] == first
    assert updated.requests[1].request_id == "request-2"
    assert updated.requests[1].outcome is RequestOutcome.REFUSED


def test_answer_before_the_deadline_is_accepted():
    updated = apply_outcome(mission_with(seat_request()), "request-1", "accepted", 6, context(19))
    assert updated.requests[0].outcome is RequestOutcome.ACCEPTED


@pytest.mark.parametrize("outcome", ["cancelled", "expired"])
def test_cancellation_and_expiry_are_not_blocked_by_the_deadline(outcome):
    updated = apply_outcome(mission_with(seat_request()), "request-1", outcome, 0, context(25))
    assert updated.requests[0].response_received_at is None
    assert updated.requests[0].closed_at == 25


REJECTIONS = (
    pytest.param(
        mission_with(seat_request()),
        "request-2",
        "accepted",
        6,
        12,
        "unknown request",
        id="unknown-request",
    ),
    pytest.param(
        mission_with(closed_request()),
        "request-1",
        "refused",
        0,
        13,
        "closed requests cannot change outcome",
        id="closed-request",
    ),
    pytest.param(
        mission_with(seat_request()),
        "request-1",
        RequestOutcome.PENDING,
        0,
        12,
        "outcome must be a supported terminal request state",
        id="non-final-pending-member",
    ),
    pytest.param(
        mission_with(seat_request()),
        "request-1",
        "pending",
        0,
        12,
        "outcome must be a supported terminal request state",
        id="non-final-pending-string",
    ),
    pytest.param(
        mission_with(seat_request()),
        "request-1",
        "bogus",
        0,
        12,
        "outcome must be a supported terminal request state",
        id="unknown-outcome-string",
    ),
    pytest.param(
        mission_with(seat_request()),
        "request-1",
        "accepted",
        7,
        12,
        "confirmation exceeds request quantity",
        id="confirmation-above-requested",
    ),
    pytest.param(
        mission_with(seat_request()),
        "request-1",
        "refused",
        -1,
        12,
        "confirmation exceeds request quantity",
        id="negative-confirmation",
    ),
    pytest.param(
        mission_with(seat_request()),
        "request-1",
        "accepted",
        6.0,
        12,
        "confirmed seats must be an integer",
        id="non-integer-confirmation",
    ),
    pytest.param(
        mission_with(seat_request()),
        "request-1",
        "accepted",
        4,
        12,
        "accepted outcome must confirm the requested quantity",
        id="accepted-with-partial",
    ),
    pytest.param(
        mission_with(seat_request()),
        "request-1",
        "partially_accepted",
        0,
        12,
        "partial acceptance must confirm a positive subset",
        id="partial-with-zero",
    ),
    pytest.param(
        mission_with(seat_request()),
        "request-1",
        "partially_accepted",
        6,
        12,
        "partial acceptance must confirm a positive subset",
        id="partial-with-full",
    ),
    pytest.param(
        mission_with(seat_request()),
        "request-1",
        "refused",
        2,
        12,
        "refused outcome cannot confirm seats",
        id="refused-with-seats",
    ),
    pytest.param(
        mission_with(seat_request()),
        "request-1",
        "cancelled",
        1,
        12,
        "cancelled outcome cannot confirm seats",
        id="cancelled-with-seats",
    ),
    pytest.param(
        mission_with(seat_request()),
        "request-1",
        "expired",
        1,
        12,
        "expired outcome cannot confirm seats",
        id="expired-with-seats",
    ),
    pytest.param(
        mission_with(seat_request()),
        "request-1",
        "accepted",
        6,
        9,
        "outcome cannot precede request submission",
        id="before-submission",
    ),
    pytest.param(
        mission_with(seat_request()),
        "request-1",
        "accepted",
        6,
        20,
        "response is at or after request deadline",
        id="accepted-at-deadline",
    ),
    pytest.param(
        mission_with(seat_request()),
        "request-1",
        "refused",
        0,
        25,
        "response is at or after request deadline",
        id="refused-after-deadline",
    ),
)


@pytest.mark.parametrize(
    ("mission", "request_id", "outcome", "confirmed", "at", "message"), REJECTIONS
)
def test_invalid_answer_is_rejected_with_its_message(
    mission, request_id, outcome, confirmed, at, message
):
    with pytest.raises(DomainValidationError) as error:
        apply_outcome(mission, request_id, outcome, confirmed, context(at))
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("mission", "transition"),
    [
        pytest.param("mission-1", context(), id="mission-is-not-a-mission"),
        pytest.param(mission_with(seat_request()), "12", id="context-is-not-a-transition"),
    ],
)
def test_requires_mission_and_transition_context(mission, transition):
    with pytest.raises(DomainValidationError) as error:
        apply_outcome(mission, "request-1", "accepted", 6, transition)
    assert str(error.value) == "apply_outcome requires Mission and TransitionContext"


@pytest.mark.parametrize(("outcome", "confirmed"), CLOSING_CASES)
def test_pending_mission_accounts_for_every_terminal_outcome(outcome, confirmed):
    mission = pending_mission()
    pending = progress(mission)
    assert pending.demand == 10
    assert pending.confirmed == 0
    assert pending.pending == 6
    assert mission.requests[0].outcome == "pending"

    changed = apply_outcome(
        mission,
        "request-1",
        outcome,
        confirmed,
        TransitionContext(event_id="outcome", at="2", reason="test"),
    )
    result = progress(changed)
    assert result.demand == 10
    assert result.confirmed == confirmed
    assert result.pending == 0
    request = changed.requests[0]
    assert request.outcome == outcome
    assert request.confirmed_seats == confirmed
    assert request.closed_at == 2
    assert [entry.event_id for entry in changed.history] == ["created", "outcome"]


def test_partial_acceptance_is_terminal_and_releases_unconfirmed_seats():
    mission = pending_mission()
    accepted = apply_outcome(
        mission,
        "request-1",
        "partially_accepted",
        4,
        TransitionContext(event_id="partial", at="2", reason="test"),
    )

    result = progress(accepted)
    assert (result.confirmed, result.pending, result.unconfirmed, result.additional_needed) == (
        4,
        0,
        6,
        6,
    )
    assert result.status == "needs_more_help"

    with pytest.raises(ValueError):
        apply_outcome(
            accepted,
            "request-1",
            "accepted",
            6,
            TransitionContext(event_id="late-outcome", at="3", reason="test"),
        )
    assert len(accepted.history) == 2


def test_full_acceptance_completes_mission_but_pending_demand_does_not():
    mission = pending_mission(seats=10)
    pending = progress(mission)
    assert pending.confirmed == 0
    assert pending.pending == 10
    assert pending.status == "awaiting_responses"

    complete = apply_outcome(
        mission,
        "request-1",
        "accepted",
        10,
        TransitionContext(event_id="accepted", at="2", reason="test"),
    )
    result = progress(complete)
    assert result.demand == 10
    assert result.confirmed == 10
    assert result.pending == 0
    assert result.additional_needed == 0
    assert result.status == "complete"


@pytest.mark.parametrize("invalid", [-1, 7, 1.5, True])
def test_invalid_confirmation_leaves_the_mission_unchanged(invalid):
    mission = pending_mission()
    original = copy.deepcopy(mission)

    with pytest.raises(ValueError):
        apply_outcome(
            mission,
            "request-1",
            "partially_accepted",
            invalid,
            TransitionContext(event_id=f"invalid-{invalid}", at="2", reason="test"),
        )
    assert progress(mission).pending == 6
    assert len(mission.history) == 1
    assert mission == original
