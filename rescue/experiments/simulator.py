"""The experiments-backed implementation of the Simulator port.

What: RunnerSimulator answers the Simulator port by calling rescue.experiments.simulation.simulate
  with the run factory it was given.
When called: constructed once by new_run in rescue/bootstrap.py and handed to RescueCentral.
Why: the composition root supplies the run factory, so neither the simulation package nor this
  adapter imports the bootstrap that builds runs (research R4, spec 009).
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from dataclasses import dataclass

from rescue.adapters.ports import Simulator
from rescue.experiments.models import RescueScenario, RunSnapshot
from rescue.experiments.simulation import simulate
from rescue.experiments.simulation.ports import StartRun
from rescue.mobilisation.models import MobilisationPolicy
from rescue.values import Id


@dataclass(frozen=True, slots=True)
class RunnerSimulator(Simulator):
    """Simulates a scenario by delegating to the simulation package with an injected run factory.

    What: holds the StartRun factory and returns the RunSnapshot the simulation produces.
    When called: once per policy compared by RescueCentral.compare, through the Simulator port.
    Why: keeps the application free of any import of the simulation package while the run factory
      still comes from the composition root (research R4).
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    start_run: StartRun

    def simulate(
        self, scenario: RescueScenario, policy: MobilisationPolicy, simulation_id: Id
    ) -> RunSnapshot:
        """Simulate the scenario under the policy with the injected run factory.

        What: calls simulate with the scenario, policy, simulation id and the held start_run.
        When called: by the compare_policies service through the Simulator port.
        Why: the simulation package receives its run factory as an argument, never by import.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        return simulate(scenario, policy, simulation_id, start_run=self.start_run)
