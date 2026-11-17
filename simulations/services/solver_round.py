"""Run real solver proposals and submit only their selected ranked allocations."""

from simulations.models.operation_command import OperationCommand
from simulations.models.operation_name import OperationName


def request_command(allocation, mission_id, now, deadline, command_id):
    """Bind a real selected evaluation to a fresh request command at submission time."""
    return OperationCommand(
        operation=OperationName.CREATE_REQUEST,
        command_id=command_id,
        mission_id=mission_id,
        ship_id=allocation.ship_id,
        requested_seats=allocation.proposed_seats,
        revision_id=allocation.revision_id,
        decision_id=allocation.decision_id,
        allocation=allocation,
        at=now,
        response_deadline=deadline,
    )


def solver_round(
    api, run_id, mission_id, policy, now, response_deadline, command_prefix, *, submit=True
):
    """Mobilise through the API, optionally submitting each returned selected allocation.

    A deferred proposal reserves no capacity. Called by timeline solver actions, this
    function keeps all allocation policy on the server and binds only observed IDs.
    """
    proposal = api.invoke(
        run_id,
        OperationCommand(
            operation=OperationName.MOBILISE,
            mission_id=mission_id,
            policy_id=policy.policy_id,
            policy_revision=policy.revision,
            at=now,
        ),
    )
    outcomes = [proposal]
    if not 200 <= proposal.http_status < 300 or proposal.application_status == "rejected":
        raise ValueError(f"Solver unavailable: {proposal.reason}")
    if submit and proposal.value is not None:
        for allocation in sorted(proposal.value.allocations, key=lambda item: item.rank):
            outcome = api.invoke(
                run_id,
                request_command(
                    allocation,
                    mission_id,
                    now,
                    response_deadline,
                    f"{command_prefix}-{allocation.rank}",
                ),
            )
            if outcome.application_status != "applied":
                raise ValueError(f"Selected request did not apply: {outcome.reason}")
            outcomes.append(outcome)
    return tuple(outcomes)
