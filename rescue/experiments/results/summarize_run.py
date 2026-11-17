"""Pure result calculation from immutable stopped-run snapshots.

What: Defines summarize, which turns a stopped RunSnapshot into a SimulationResult.
When called: Imported by the simulation session and by tests that summarize a finished run.
Why: Summarizing is a pure calculation with no I/O, so it stays in the domain.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
"""

from __future__ import annotations

from rescue.experiments.models import RunSnapshot, SimulationResult
from rescue.market.models.offers import ShipOfferRevision
from rescue.market.models.quotes import RFQOffer
from rescue.mission.models import HistoryAction, Mission
from rescue.mission.rules import progress
from rescue.values import DomainValidationError

_TERMINAL_ACTIONS = frozenset(
    {
        HistoryAction.ACCEPTED,
        HistoryAction.PARTIALLY_ACCEPTED,
        HistoryAction.REFUSED,
        HistoryAction.CANCELLED,
        HistoryAction.EXPIRED,
    }
)


def _revision(mission: Mission, request, snapshot: RunSnapshot) -> ShipOfferRevision | None:
    """Find the offer revision a request was sent against.

    What: Returns the matching ShipOfferRevision or None.
    Why: The arrival estimate lives on the revision when no quote exists.
    """
    if request.revision_id is None:
        return None
    return next(
        (
            revision
            for offer in snapshot.market.offers
            if offer.mission_id == mission.mission_id and offer.ship_id == request.ship_id
            for revision in offer.revisions
            if revision.revision_id == request.revision_id
        ),
        None,
    )


def _arrival_instant(mission: Mission, request, snapshot: RunSnapshot):
    """Compute when the ship of a request is expected to arrive.

    What: Prefers the RFQ quote's recorded_at plus arrival estimate, else the revision's.
    Why: Quotes supersede offer revisions as the latest arrival estimate.
    """
    if request.quote_id is not None:
        quote = next(
            (item for item in snapshot.market.quotes if item.offer_id == request.quote_id),
            None,
        )
        if isinstance(quote, RFQOffer):
            return quote.recorded_at + quote.arrival_estimate_seconds
    revision = _revision(mission, request, snapshot)
    if revision is None:
        return None
    return revision.recorded_at + revision.arrival_estimate_seconds


def summarize(run: RunSnapshot) -> SimulationResult:
    """Calculate business metrics without changing the supplied run snapshot.

    What: Returns a SimulationResult with confirmed seats, unmet demand, requests sent, released
      seats, elapsed confirmation time and latest arrival estimate.
    When called: Once a run has stopped and its RunSnapshot is available.
    Why: Results compare mobilisation policies without mutating the run they describe.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Experiments/class-diagram.mmd
    """
    if not isinstance(run, RunSnapshot):
        raise DomainValidationError("summarize requires a RunSnapshot")
    missions = run.missions
    if not missions:
        raise DomainValidationError("a simulation result requires at least one mission")
    started_at = run.run.started_at
    finished_at = run.run.finished_at
    if finished_at is None or run.run.status == "running":
        raise DomainValidationError("only stopped run snapshots can be summarized")

    progress_values = tuple(progress(mission) for mission in missions)
    confirmed = sum(value.confirmed for value in progress_values)
    unmet = sum(value.demand - value.confirmed for value in progress_values)
    completed = unmet == 0
    requests_sent = 0
    released_seats = 0
    for mission in missions:
        requests_sent += sum(
            entry.action == HistoryAction.REQUEST_CREATED and entry.recorded_at >= started_at
            for entry in mission.history
        )
        released_seats += sum(
            max(0, -entry.pending_seats_delta - entry.confirmed_seats_delta)
            for entry in mission.history
            if entry.action in _TERMINAL_ACTIONS and entry.recorded_at >= started_at
        )

    confirmation_elapsed = finished_at - started_at if completed else None
    confirmed_arrivals = tuple(
        arrival
        for mission in missions
        for request in mission.requests
        if request.confirmed_seats > 0
        and request.closed_at is not None
        and request.closed_at >= started_at
        for arrival in (_arrival_instant(mission, request, run),)
        if arrival is not None
    )
    latest_arrival = max(confirmed_arrivals) - started_at if confirmed_arrivals else None
    if latest_arrival is not None and latest_arrival < 0:
        latest_arrival = 0
    return SimulationResult(
        completed=completed,
        confirmed_seats=confirmed,
        unmet_demand=unmet,
        requests_sent=requests_sent,
        released_seats=released_seats,
        confirmation_elapsed_seconds=confirmation_elapsed,
        latest_arrival_estimate_seconds=latest_arrival,
    )
