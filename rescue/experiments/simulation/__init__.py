"""The simulation package: the run-a-scenario entry point and its injected ports.

What: re-exports `simulate` and the ports `StartRun`, `RunHandle` and `SimulationCentral`.
When called: imported by the application's compare service, the demo, and tests that run a
  scenario.
Why: one import point keeps callers independent of the folder layout; the ports let experiments
  receive its run factory without importing the composition root.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from rescue.experiments.simulation.ports import RunHandle, SimulationCentral, StartRun
from rescue.experiments.simulation.run_simulation import simulate

__all__ = ["RunHandle", "SimulationCentral", "StartRun", "simulate"]
