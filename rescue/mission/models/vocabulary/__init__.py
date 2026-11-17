"""Closed vocabularies for mission outcomes, statuses and history actions.

What: re-exports RequestOutcome, ProgressStatus and HistoryAction.
When called: imported by mission models and rules, and by callers that compare outcomes.
Why: a fixed name set keeps a typo from reaching seat accounting or stored history.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from rescue.mission.models.vocabulary.history_action import HistoryAction
from rescue.mission.models.vocabulary.progress_status import ProgressStatus
from rescue.mission.models.vocabulary.request_outcome import RequestOutcome

__all__ = ["HistoryAction", "ProgressStatus", "RequestOutcome"]
