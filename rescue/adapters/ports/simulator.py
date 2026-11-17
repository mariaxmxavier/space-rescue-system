"""The ``Simulator`` port: how the application asks for a simulated run.

What: declares one operation that turns a scenario and a policy into a run snapshot.

When: held by the simulation use case of the application layer; implemented by an adapter over
the experiments simulation package.

Why: keeps the application from importing the simulation package (FR-006), so the application
names the capability and never imports the runner.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from rescue.experiments.models import RescueScenario, RunSnapshot
from rescue.mobilisation.models import MobilisationPolicy
from rescue.values import Id


class Simulator(ABC):
    """Runs one simulation of a scenario under a mobilisation policy.

    What: answers "what happens if this scenario is played under this policy".

    When: called by the application once per requested simulation, with an id from the
    ``IdSource``.

    Why: the simulation engine is an outside detail; hiding it behind a port keeps the
    application independent of it and lets tests substitute a fake.
    """

    @abstractmethod
    def simulate(
        self, scenario: RescueScenario, policy: MobilisationPolicy, simulation_id: Id
    ) -> RunSnapshot:
        """Simulate the scenario under the policy.

        What: a ``RunSnapshot`` of the simulated run identified by ``simulation_id``.

        When: called when a caller asks for a simulation of a scenario.

        Why: one place owns how a simulation is produced, so every caller gets the same result
        shape.
        """
