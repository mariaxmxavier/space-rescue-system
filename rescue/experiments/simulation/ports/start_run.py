"""The factory that starts one empty run for a simulation.

What: a Protocol for a callable taking the run id, the central id and, by keyword, the policies,
  scenarios and reserved ids, and returning a `RunHandle`.
When called: passed to `simulate` as `start_run`; called once per simulation.
Why: the caller supplies the run factory, so experiments does not import the bootstrap that
  builds runs.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from __future__ import annotations

from typing import Protocol

from rescue.experiments.models import RescueScenario
from rescue.experiments.simulation.ports.run_handle import RunHandle
from rescue.mobilisation.models import MobilisationPolicy
from rescue.values import Id


class StartRun(Protocol):
    """The factory that starts one empty run for a simulation.

    What: a callable `(application_run_id, central_id, *, policies, scenarios, reserved_ids)`
      that returns a `RunHandle`.
    When called: invoked by `simulate` once per simulation.
    Why: it lets the composition root decide how a run is built while the runner depends only on
      this shape.
    Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
    """

    def __call__(
        self,
        application_run_id: Id,
        central_id: Id,
        *,
        policies: tuple[MobilisationPolicy, ...],
        scenarios: tuple[RescueScenario, ...],
        reserved_ids: tuple[Id, ...],
    ) -> RunHandle: ...
