"""Ports the simulation runner depends on.

What: re-exports `StartRun`, `RunHandle` and `SimulationCentral`, one Protocol per module.
When called: imported by `rescue.experiments.simulation` and by callers that type a run factory.
Why: the runner depends on these shapes, so the composition root can inject any run that fits.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from rescue.experiments.simulation.ports.run_handle import RunHandle
from rescue.experiments.simulation.ports.simulation_central import SimulationCentral
from rescue.experiments.simulation.ports.start_run import StartRun

__all__ = ["RunHandle", "SimulationCentral", "StartRun"]
