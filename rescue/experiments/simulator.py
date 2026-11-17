"""The runner-backed implementation of the Simulator port.

What: RunnerSimulator answers the Simulator port by calling rescue.experiments.runner.simulate.
When called: constructed by new_run and handed to RescueCentral for policy comparison.
Why: runner imports bootstrap at module level; the lazy import is temporary until 009 injects the run factory (R4).
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from rescue.adapters.ports import Simulator
from rescue.experiments.models import RescueScenario, RunSnapshot
from rescue.mobilisation.models import MobilisationPolicy
from rescue.values import Id


class RunnerSimulator(Simulator):
    """Simulates a scenario by delegating to the experiment runner.

    What: returns the RunSnapshot the runner produces for the scenario and policy.
    When called: once per policy compared by RescueCentral.compare.
    Why: runner imports bootstrap at module level; the lazy import is temporary until 009 injects the run factory (R4).
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def simulate(
        self, scenario: RescueScenario, policy: MobilisationPolicy, simulation_id: Id
    ) -> RunSnapshot:
        """Simulate the scenario under the policy.

        What: delegates to rescue.experiments.runner.simulate.
        When called: by the compare_policies service through the Simulator port.
        Why: runner imports bootstrap at module level; the lazy import is temporary until 009 injects the run factory (R4).
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        from rescue.experiments.runner import simulate

        return simulate(scenario, policy, simulation_id)
