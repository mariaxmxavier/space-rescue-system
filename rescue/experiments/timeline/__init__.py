"""Finite deterministic timeline of simulated scenario events.

What: re-exports Timeline and TimelineEvent so existing import paths keep working.
When called: imported whenever a module reads rescue.experiments.timeline.
Why: the heap scheduler is pure domain code; the package keeps its public import path stable.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from rescue.experiments.timeline.timeline import Timeline
from rescue.experiments.timeline.timeline_event import TimelineEvent

__all__ = ["Timeline", "TimelineEvent"]
