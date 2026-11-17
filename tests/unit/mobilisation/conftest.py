"""Reusable immutable values for mobilisation rule and allocator tests."""

from __future__ import annotations

from types import MappingProxyType
from typing import Callable

import pytest

from rescue.market.models import RFQOffer, ShipOfferRevision
from rescue.mission.models import Mission, SeatRequest
from rescue.mobilisation.models import Candidate, DecisionContext, MobilisationPolicy


def _mission(demand: int = 10, *, pending: int = 0, confirmed: int = 0) -> Mission:
    """Build an immutable mission with optional pending and accepted commitments."""
    requests: list[SeatRequest] = []
    if pending:
        requests.append(
            SeatRequest(
                request_id="pending-request",
                command_id="pending-command",
                mission_id="mission-1",
                ship_id="pending-ship",
                requested_seats=pending,
                confirmed_seats=0,
                outcome="pending",
                submitted_at=1,
                revision_id="pending-revision",
            )
        )
    if confirmed:
        requests.append(
            SeatRequest(
                request_id="confirmed-request",
                command_id="confirmed-command",
                mission_id="mission-1",
                ship_id="confirmed-ship",
                requested_seats=confirmed,
                confirmed_seats=confirmed,
                outcome="accepted",
                submitted_at=1,
                response_received_at=2,
                revision_id="confirmed-revision",
            )
        )
    return Mission(
        mission_id="mission-1",
        station_name="Station One",
        people_count=demand,
        created_at=0,
        requests=tuple(requests),
    )


def _revision(
    revision_id: str,
    *,
    capacity: int = 10,
    arrival: int = 0,
    recorded_at: int = 0,
    available: bool = True,
) -> ShipOfferRevision:
    """Build a ship offer revision for a fixed arrival and availability snapshot."""
    return ShipOfferRevision(
        revision_id=revision_id,
        revision_number=1,
        capacity=capacity,
        arrival_estimate_seconds=arrival,
        available=available,
        recorded_at=recorded_at,
    )


def _quote(
    offer_id: str,
    offered_seats: int,
    *,
    expires_at: int = 20,
    recorded_at: int = 1,
    status: str = "held",
) -> RFQOffer:
    """Build a held, expired, or closed quote with valid market value constraints."""
    return RFQOffer(
        offer_id=offer_id,
        rfq_id=f"rfq-{offer_id}",
        offered_seats=offered_seats,
        arrival_estimate_seconds=1,
        expires_at=expires_at,
        recorded_at=recorded_at,
        status=status,
        request_id="accepted-request" if status == "accepted" else None,
    )


def _candidate(
    ship_id: str,
    revision: ShipOfferRevision,
    *,
    free_seats: int = 10,
    quote: RFQOffer | None = None,
) -> Candidate:
    """Build a candidate whose allocatable capacity reflects both snapshots."""
    return Candidate(ship_id=ship_id, revision=revision, free_seats=free_seats, quote=quote)


def _policy(strategy: str = "earliest_arrival") -> MobilisationPolicy:
    """Build a policy for a named current or planned allocator."""
    return MobilisationPolicy(
        policy_id=f"policy-{strategy}",
        revision=1,
        name=strategy.replace("_", " ").title(),
        selection_criteria=strategy,
    )


def _context(candidate_count: int, *, recorded_at: int = 0) -> DecisionContext:
    """Build a decision context with one stable evaluation id per candidate."""
    return DecisionContext(
        decision_id="decision-1",
        recorded_at=recorded_at,
        evaluation_ids=tuple(f"evaluation-{index}" for index in range(1, candidate_count + 1)),
    )


@pytest.fixture
def mission_factory() -> Callable[..., Mission]:
    """Provide a factory for missions with explicit pending and confirmed quantities."""
    return _mission


@pytest.fixture
def revision_factory() -> Callable[..., ShipOfferRevision]:
    """Provide a factory for immutable ship revision snapshots."""
    return _revision


@pytest.fixture
def quote_factory() -> Callable[..., RFQOffer]:
    """Provide a factory for held, expired, rejected, and accepted quote snapshots."""
    return _quote


@pytest.fixture
def candidate_factory() -> Callable[..., Candidate]:
    """Provide a factory for immutable mobilisation candidates."""
    return _candidate


@pytest.fixture
def policy_factory() -> Callable[..., MobilisationPolicy]:
    """Provide a factory for mobilisation policy values."""
    return _policy


@pytest.fixture
def decision_context_factory() -> Callable[..., DecisionContext]:
    """Provide a factory for contexts with exactly one evaluation id per candidate."""
    return _context


@pytest.fixture
def mobilisation_scenarios(
    mission_factory,
    revision_factory,
    quote_factory,
    candidate_factory,
    policy_factory,
    decision_context_factory,
):
    """Return immutable edge scenarios shared by allocator contract tests."""
    no_candidates = ()
    covered_candidates = (candidate_factory("covered", revision_factory("covered-r")),)
    unavailable_and_empty = (
        candidate_factory(
            "unavailable",
            revision_factory("unavailable-r", available=False),
        ),
        candidate_factory("empty", revision_factory("empty-r"), free_seats=0),
    )
    unusable_quotes = (
        candidate_factory(
            "rejected",
            revision_factory("rejected-r"),
            quote=quote_factory("rejected-q", 2, status="rejected"),
        ),
        candidate_factory(
            "expired",
            revision_factory("expired-r"),
            quote=quote_factory("expired-q", 2, expires_at=5),
        ),
    )
    oversized_quote = (
        candidate_factory(
            "oversized",
            revision_factory("oversized-r", capacity=6),
            quote=quote_factory("oversized-q", 6),
        ),
    )
    tied = tuple(
        candidate_factory(ship_id, revision_factory(f"tie-{ship_id}", arrival=5))
        for ship_id in ("C", "A", "B")
    )
    partial_capacity = (
        candidate_factory("partial-a", revision_factory("partial-a-r", capacity=4)),
        candidate_factory(
            "partial-b",
            revision_factory("partial-b-r", capacity=3),
            free_seats=5,
        ),
    )
    indivisible = (
        candidate_factory(
            "quote-five",
            revision_factory("quote-five-r", capacity=5, arrival=1),
            quote=quote_factory("quote-five-q", 5),
        ),
        candidate_factory(
            "quote-four",
            revision_factory("quote-four-r", capacity=4, arrival=2),
            quote=quote_factory("quote-four-q", 4),
        ),
    )

    cases = {
        "empty_inputs": (
            mission_factory(7),
            no_candidates,
            policy_factory(),
            decision_context_factory(0),
        ),
        "covered_demand": (
            mission_factory(10, pending=6, confirmed=4),
            covered_candidates,
            policy_factory(),
            decision_context_factory(1),
        ),
        "exhausted_and_unavailable": (
            mission_factory(5),
            unavailable_and_empty,
            policy_factory(),
            decision_context_factory(2),
        ),
        "invalid_and_expired_holds": (
            mission_factory(5),
            unusable_quotes,
            policy_factory(),
            decision_context_factory(2, recorded_at=5),
        ),
        "oversized_hold": (
            mission_factory(5),
            oversized_quote,
            policy_factory(),
            decision_context_factory(1),
        ),
        "deterministic_ties": (
            mission_factory(3),
            tied,
            policy_factory(),
            decision_context_factory(3),
        ),
        "partial_capacity": (
            mission_factory(6),
            partial_capacity,
            policy_factory(),
            decision_context_factory(2),
        ),
        "indivisible_undercoverage": (
            mission_factory(7),
            indivisible,
            policy_factory("knapsack"),
            decision_context_factory(2),
        ),
    }
    return MappingProxyType(cases)
