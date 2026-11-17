"""Closed vocabulary of mission progress statuses.

What: the set of statuses a mission's seat progress can report, as a StrEnum.
When called: returned as the status of a mission's progress and compared by
  callers that report it.
Why: one spelling per status keeps the rules, the views and the diagrams from drifting apart.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from __future__ import annotations

from enum import StrEnum


class ProgressStatus(StrEnum):
    """Progress of a mission's seats: complete, awaiting responses, or needing more help.

    What: the three progress statuses, each equal to its wire string.
    When called: returned with a mission's progress; callers compare against these
      members instead of string literals.
    Why: a status outside this set fails at construction, so pending seats can never
      be reported as complete (Constitution I).
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
    """

    COMPLETE = "complete"
    AWAITING_RESPONSES = "awaiting_responses"
    NEEDS_MORE_HELP = "needs_more_help"
