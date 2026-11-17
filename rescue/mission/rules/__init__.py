"""Pure mission transitions and seat-accounting rules.

What: re-exports the five mission rules under one import path.
When called: imported by application, experiments, mobilisation, demo and tests as rescue.mission.rules.
Why: one stable import path for every caller of the seat-accounting rules.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""

from rescue.mission.rules.add_request import add_request
from rescue.mission.rules.apply_outcome import apply_outcome
from rescue.mission.rules.progress import progress
from rescue.mission.rules.register import register
from rescue.mission.rules.timing import timing

__all__ = ["add_request", "apply_outcome", "progress", "register", "timing"]
