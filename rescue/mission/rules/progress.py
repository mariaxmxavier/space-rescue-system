"""Seat progress rule: the demand, confirmed and pending seats of a mission, read without change.

What: derives the seat accounting of a mission and the progress status those counts imply.
When called: by the application and the views each time a mission's progress is shown; the
  mission itself is never written.
Why: progress is a projection of the requests, so reading it can never alter a seat count or a
  history row (Constitution I).
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from __future__ import annotations

from rescue.mission.models.mission.mission import Mission
from rescue.mission.models.projections.mission_progress import MissionProgress
from rescue.mission.models.vocabulary.progress_status import ProgressStatus
from rescue.mission.rules._accounting import account
from rescue.values import DomainValidationError


def progress(mission: Mission) -> MissionProgress:
    """Return the seat progress of a mission, leaving the mission untouched.

    What: sums the confirmed and pending seats, then reports complete when every demanded seat is
      confirmed, awaiting responses when confirmed and pending seats cover the demand, and needs
      more help otherwise.
    When called: by the application and the views to show how many seats still need a ship.
    Why: the status is computed from the same accounting that guards every transition, so a
      mission with pending seats can never read as complete (Constitution I).
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """
    if not isinstance(mission, Mission):
        raise DomainValidationError("progress requires a Mission")
    confirmed, pending = account(mission)
    demand = mission.people_count
    status = (
        ProgressStatus.COMPLETE
        if confirmed == demand
        else ProgressStatus.AWAITING_RESPONSES
        if confirmed + pending == demand
        else ProgressStatus.NEEDS_MORE_HELP
    )
    return MissionProgress(
        demand=demand,
        confirmed=confirmed,
        pending=pending,
        unconfirmed=demand - confirmed,
        additional_needed=demand - confirmed - pending,
        status=status,
    )
