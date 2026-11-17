"""Run one real mobilisation proposal and optionally create its selected requests."""

from decimal import Decimal

from simulations.adapters.ports.mission_api import MissionApiABC
from simulations.models.operation_command import OperationCommand
from simulations.models.operation_name import OperationName
from simulations.models.operation_outcome import OperationOutcome
from simulations.models.policy_setup import PolicySetup


def solver_round(
    api: MissionApiABC,
    run_id: str,
    mission_id: str,
    policy: PolicySetup,
    now: Decimal,
    response_deadline: Decimal,
    command_prefix: str,
    *,
    submit: bool = True,
) -> tuple[OperationOutcome, ...]:
    """Mobilise through the API and submit selected allocations in rank order.

    A proposal does not reserve seats. When ``submit`` is false, the returned
    tuple contains only the mobilisation outcome so callers can explicitly
    defer request creation while another timeline event is pending.
    """
    proposal = api.invoke(
        run_id,
        OperationCommand(
            operation=OperationName.MOBILISE,
            command_id=f"{command_prefix}-mobilise",
            mission_id=mission_id,
            policy=policy,
            at=now,
        ),
    )
    outcomes = [proposal]
    if not submit or not 200 <= proposal.http_status < 300 or proposal.value is None:
        return tuple(outcomes)

    allocations = getattr(proposal.value, "allocations", ())
    for allocation in sorted(allocations, key=lambda item: item.rank):
        outcomes.append(
            api.invoke(
                run_id,
                OperationCommand(
                    operation=OperationName.CREATE_REQUEST,
                    command_id=f"{command_prefix}-request-{allocation.rank}",
                    mission_id=mission_id,
                    allocation=allocation,
                    requested_seats=allocation.proposed_seats,
                    response_deadline=response_deadline,
                    at=now,
                ),
            )
        )
    return tuple(outcomes)
