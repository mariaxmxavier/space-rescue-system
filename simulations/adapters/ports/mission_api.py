"""Abstract boundary for running a mission through the rescue HTTP API."""

from abc import ABC, abstractmethod
from decimal import Decimal

from simulations.models.api_state import ApiState
from simulations.models.mission_progress import MissionProgress
from simulations.models.operation_command import OperationCommand
from simulations.models.operation_outcome import OperationOutcome
from simulations.models.policy_setup import PolicySetup


class MissionApiABC(ABC):
    """Define the injected operations required by simulation services."""

    @abstractmethod
    def create_run(self, namespace: str, policy: PolicySetup) -> OperationOutcome:
        """Create a fresh server run using a unique execution namespace."""

    @abstractmethod
    def invoke(self, run_id: str, command: OperationCommand) -> OperationOutcome:
        """Submit one typed operation and return its HTTP/application outcome."""

    @abstractmethod
    def progress(self, run_id: str, mission_id: str, at: Decimal) -> MissionProgress:
        """Read authoritative progress for the mission after an event."""

    @abstractmethod
    def state(self, run_id: str) -> ApiState:
        """Read typed request, session and delivery projections when evidence requires them."""

    @abstractmethod
    def invoke_batch(
        self, run_id: str, commands: tuple[OperationCommand, ...]
    ) -> tuple[OperationOutcome, ...]:
        """Invoke one batch of one or two concurrent operations and join their outcomes."""
