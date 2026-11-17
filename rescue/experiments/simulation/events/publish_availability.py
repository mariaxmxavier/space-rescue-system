"""Publish a scheduled availability change.

What: sends the event's availability to the central and fails on a rejected publication.
When called: when the timeline pops an "availability" event.
Why: scenario availability changes must reach the market or the run is invalid.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from __future__ import annotations

from decimal import Decimal

from rescue.application.contracts import PublishAvailability
from rescue.experiments.simulation.session import SimulationSession
from rescue.experiments.timeline import TimelineEvent
from rescue.values import DomainValidationError


def publish_availability(session: SimulationSession, event: TimelineEvent, now: Decimal) -> None:
    """Publish a scheduled availability change.

    What: calls the central's `publish_availability` with the event payload.
    When called: for each "availability" timeline event.
    Why: a failed publication raises, so a broken scenario stops instead of running on.
    Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
    """
    publication = session.handle.central.publish_availability(
        PublishAvailability(availability=event.payload)
    )
    if publication.status not in {"applied", "replayed"}:
        raise DomainValidationError(f"scenario availability change failed: {publication.reason}")
