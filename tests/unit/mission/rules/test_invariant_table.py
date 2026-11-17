"""Invariant table: every final outcome against every reachable seat request state.

What: one parametrised table that applies each of the five final outcomes to a pending request for
  one seat, for a middle count and for all seats of a demand, and to each closed outcome as a fixed
  state, then checks the seat rules after every transition.
When called: collected by pytest on every run of the mission rule tests.
Why: the seat invariant (C >= 0, P >= 0, C + P <= D) and the rule that a closed request is final
  must hold for every combination the rules can reach, not only for the cases one test picks.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from dataclasses import replace

import pytest

from rescue.mission.models.mission.mission import Mission
from rescue.mission.models.mission.mission_data import MissionData
from rescue.mission.models.mission.seat_request import SeatRequest
from rescue.mission.models.vocabulary.request_outcome import RequestOutcome
from rescue.mission.rules.add_request import add_request
from rescue.mission.rules.apply_outcome import apply_outcome
from rescue.mission.rules.register import register
from rescue.values import DomainValidationError, TransitionContext

DEMAND = 6
ONE_SEAT = 1
MIDDLE_SEATS = 3
REQUEST_ID = "request-1"
REASON = "seat rule table"
CLOSED_REJECTION = "closed requests cannot change outcome"
PARTIAL_REJECTION = "partial acceptance must confirm a positive subset"
CONFIRMATION_REJECTION = "confirmation exceeds request quantity"

MISSION = MissionData(
    mission_id="mission-1", station_name="Station A", people_count=DEMAND, created_at=0
)
SUBMISSION = TransitionContext(event_id="request-1", at=10, reason=REASON)
ANSWER = TransitionContext(event_id="answer-1", at=12, reason=REASON)

CONFIRMED_BY_OUTCOME = {
    RequestOutcome.ACCEPTED: MIDDLE_SEATS,
    RequestOutcome.PARTIALLY_ACCEPTED: 1,
    RequestOutcome.REFUSED: 0,
    RequestOutcome.CANCELLED: 0,
    RequestOutcome.EXPIRED: 0,
}

OUT_OF_ORDER = (
    (RequestOutcome.ACCEPTED, RequestOutcome.REFUSED),
    (RequestOutcome.PARTIALLY_ACCEPTED, RequestOutcome.ACCEPTED),
    (RequestOutcome.REFUSED, RequestOutcome.CANCELLED),
    (RequestOutcome.CANCELLED, RequestOutcome.EXPIRED),
    (RequestOutcome.EXPIRED, RequestOutcome.PARTIALLY_ACCEPTED),
)


def seat_request(requested_seats):
    """Return a pending request for the given seats, with no confirmed seats.

    What: a pending SeatRequest owned by the table mission.
    Why: every row starts from the same request, so only the outcome under test varies.
    """
    return SeatRequest(
        request_id=REQUEST_ID,
        command_id="command-1",
        mission_id="mission-1",
        ship_id="ship-1",
        requested_seats=requested_seats,
        confirmed_seats=0,
        outcome=RequestOutcome.PENDING,
        submitted_at=10,
        response_deadline=20,
    )


def pending_mission(requested_seats):
    """Return the table mission registered and holding one pending request.

    What: registers the mission, then adds the pending request for the given seats.
    Why: every reachable state starts from a registered mission with one request added.
    """
    return add_request(register(MISSION), seat_request(requested_seats), SUBMISSION)


def seat_totals(mission: Mission) -> tuple[int, int]:
    """Return the confirmed and pending seat totals, summed from the mission's requests.

    What: C is the sum of confirmed seats, P the sum of requested seats of pending requests.
    Why: the table checks the invariant from the stored requests, not from the rule under test.
    """
    confirmed = sum(request.confirmed_seats for request in mission.requests)
    pending = sum(
        request.requested_seats
        for request in mission.requests
        if request.outcome is RequestOutcome.PENDING
    )
    return confirmed, pending


def assert_seat_invariant(mission: Mission) -> None:
    """Assert that C >= 0, P >= 0 and C + P <= D hold for the mission.

    What: checks the three seat inequalities against the mission's demand.
    Why: the invariant is what keeps every promised seat real, so it is checked after each step.
    """
    confirmed, pending = seat_totals(mission)
    assert confirmed >= 0
    assert pending >= 0
    assert confirmed + pending <= mission.people_count


def assert_rejected(mission: Mission, outcome, confirmed, message: str) -> None:
    """Assert that applying an outcome raises the named rejection and leaves the mission unchanged.

    What: applies the outcome, expects a DomainValidationError with the given message, and checks
      that the mission still equals a copy of itself taken before the call.
    Why: a rejected transition must return no new mission and must not alter the one the caller
      holds, so the seat rules keep holding for it.
    """
    before = replace(mission)
    with pytest.raises(DomainValidationError) as error:
        apply_outcome(mission, REQUEST_ID, outcome, confirmed, ANSWER)
    assert str(error.value) == message
    assert mission == before
    assert_seat_invariant(mission)


def assert_closed_is_final(closed: Mission) -> None:
    """Assert that every final outcome is rejected on a closed request.

    What: applies each of the five final outcomes to the closed request and expects the
      closed-request rejection each time.
    Why: a closed request is final, so no later answer, cancellation or expiry may change it.
    """
    for outcome in RequestOutcome.final():
        assert_rejected(closed, outcome, 0, CLOSED_REJECTION)


def pending_row(requested, outcome, confirmed, rejection=None):
    """Return one table row for a pending request meeting a final outcome.

    What: a parametrise entry with no closing outcome, the outcome, the confirmed seats and the
      expected rejection, if any.
    Why: a row names exactly what the rules must do for that pending state and outcome.
    """
    return pytest.param(
        requested, None, outcome, confirmed, rejection, id=f"pending-{requested}-{outcome.value}"
    )


PENDING_ROWS = (
    pending_row(ONE_SEAT, RequestOutcome.ACCEPTED, 1),
    pending_row(ONE_SEAT, RequestOutcome.PARTIALLY_ACCEPTED, 0, PARTIAL_REJECTION),
    pending_row(ONE_SEAT, RequestOutcome.REFUSED, 0),
    pending_row(ONE_SEAT, RequestOutcome.CANCELLED, 0),
    pending_row(ONE_SEAT, RequestOutcome.EXPIRED, 0),
    pending_row(MIDDLE_SEATS, RequestOutcome.ACCEPTED, 3),
    pending_row(MIDDLE_SEATS, RequestOutcome.PARTIALLY_ACCEPTED, 1),
    pending_row(MIDDLE_SEATS, RequestOutcome.REFUSED, 0),
    pending_row(MIDDLE_SEATS, RequestOutcome.CANCELLED, 0),
    pending_row(MIDDLE_SEATS, RequestOutcome.EXPIRED, 0),
    pending_row(DEMAND, RequestOutcome.ACCEPTED, 6),
    pending_row(DEMAND, RequestOutcome.PARTIALLY_ACCEPTED, 3),
    pending_row(DEMAND, RequestOutcome.REFUSED, 0),
    pending_row(DEMAND, RequestOutcome.CANCELLED, 0),
    pending_row(DEMAND, RequestOutcome.EXPIRED, 0),
)

CLOSED_ROWS = tuple(
    pytest.param(
        MIDDLE_SEATS,
        closing,
        outcome,
        CONFIRMED_BY_OUTCOME[outcome],
        CLOSED_REJECTION,
        id=f"closed-{closing.value}-then-{outcome.value}",
    )
    for closing in RequestOutcome.final()
    for outcome in RequestOutcome.final()
)

ROWS = PENDING_ROWS + CLOSED_ROWS


@pytest.mark.parametrize(("requested", "closing", "outcome", "confirmed", "rejection"), ROWS)
def test_each_final_outcome_keeps_the_seat_rules_for_every_reachable_state(
    requested, closing, outcome, confirmed, rejection
):
    """Apply one final outcome to one reachable state and check the seat rules after each step.

    What: builds the pending request, closes it first when the row names a closing outcome, then
      applies the row's outcome. A rejected row must raise its rejection; an accepted row must
      release the unconfirmed seats and then refuse every further outcome.
    When called: by pytest once for each row of ROWS.
    Why: the seat invariant and the rule that a closed request is final must hold for every final
      outcome in every reachable state, not only for the cases each rule test happens to pick.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """
    mission = pending_mission(requested)
    if closing is not None:
        mission = apply_outcome(mission, REQUEST_ID, closing, CONFIRMED_BY_OUTCOME[closing], ANSWER)
    assert_seat_invariant(mission)
    if rejection is not None:
        assert_rejected(mission, outcome, confirmed, rejection)
        return
    updated = apply_outcome(mission, REQUEST_ID, outcome, confirmed, ANSWER)
    assert_seat_invariant(updated)
    assert seat_totals(updated) == (confirmed, 0)
    assert updated.requests[0].outcome is outcome
    assert_closed_is_final(updated)


def test_refusal_releases_the_seats_a_zero_confirmed_partial_acceptance_would_release():
    """Check that refusal frees the whole pending share, since zero-confirmed partial is invalid.

    What: rejects partial acceptance with zero confirmed seats, then refuses the same request and
      checks the released pending count and the confirmed count.
    When called: by pytest once, for the spec edge case on partial acceptance with zero confirmed.
    Why: a ship that confirms nothing must free its whole share through refusal, because a
      partial acceptance with zero confirmed seats is not a valid outcome.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """
    mission = pending_mission(MIDDLE_SEATS)
    assert_rejected(mission, RequestOutcome.PARTIALLY_ACCEPTED, 0, PARTIAL_REJECTION)
    refused = apply_outcome(mission, REQUEST_ID, RequestOutcome.REFUSED, 0, ANSWER)
    confirmed_before, pending_before = seat_totals(mission)
    confirmed_after, pending_after = seat_totals(refused)
    assert pending_before - pending_after == MIDDLE_SEATS
    assert pending_after == 0
    assert confirmed_before == confirmed_after == 0
    assert refused.requests[0].outcome is RequestOutcome.REFUSED
    assert refused.history[-1].pending_seats_delta == -MIDDLE_SEATS


@pytest.mark.parametrize("outcome", RequestOutcome.final())
def test_confirmation_above_requested_is_rejected_and_changes_nothing(outcome):
    """Check that confirming more seats than requested is rejected for every final outcome.

    What: applies each final outcome with one seat more than requested and expects the
      confirmation rejection, with the request still pending and unchanged.
    When called: by pytest once for each final outcome.
    Why: a ship cannot confirm seats it was never asked for, so no outcome may promise them.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """
    mission = pending_mission(MIDDLE_SEATS)
    assert_rejected(mission, outcome, MIDDLE_SEATS + 1, CONFIRMATION_REJECTION)
    assert mission.requests == (seat_request(MIDDLE_SEATS),)


@pytest.mark.parametrize("outcome", RequestOutcome.final())
def test_repeated_outcome_on_a_closed_request_is_rejected(outcome):
    """Check that the same outcome cannot be applied twice to one request.

    What: closes the request with a final outcome, then applies that same outcome again and expects
      the closed-request rejection with the mission unchanged.
    When called: by pytest once for each final outcome.
    Why: a closed request is final, so a repeated answer must not add seats or history again.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """
    closed = apply_outcome(
        pending_mission(MIDDLE_SEATS), REQUEST_ID, outcome, CONFIRMED_BY_OUTCOME[outcome], ANSWER
    )
    assert_rejected(closed, outcome, CONFIRMED_BY_OUTCOME[outcome], CLOSED_REJECTION)


@pytest.mark.parametrize(("first", "later"), OUT_OF_ORDER)
def test_out_of_order_outcome_on_a_closed_request_is_rejected(first, later):
    """Check that a different outcome arriving after the request closed is rejected.

    What: closes the request with one final outcome, then applies another final outcome and expects
      the closed-request rejection with the mission unchanged.
    When called: by pytest once for each out-of-order pair in OUT_OF_ORDER.
    Why: an answer that arrives after the request has closed must not overturn the closed outcome.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """
    closed = apply_outcome(
        pending_mission(MIDDLE_SEATS), REQUEST_ID, first, CONFIRMED_BY_OUTCOME[first], ANSWER
    )
    assert_rejected(closed, later, CONFIRMED_BY_OUTCOME[later], CLOSED_REJECTION)
