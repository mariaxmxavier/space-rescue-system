"""Run configured policies against one immutable scenario revision.

What: validates the policy keys, reads one store snapshot, and simulates each policy on the scenario.
When called: by RescueCentral.compare, which hands the ComparePolicies command to this service.
Why: experiments need every policy run on the same scenario, and the store lock is released before any simulation starts.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from rescue.adapters.ports import IdSource, Simulator, TransactionStore
from rescue.application.contracts import ComparePolicies, Result
from rescue.application.shared.make_result import make_result
from rescue.values import DomainValidationError, normalize_id, normalize_positive_quantity


def compare_policies(
    command: ComparePolicies,
    *,
    store: TransactionStore,
    id_source: IdSource,
    simulator: Simulator,
) -> Result:
    """Compare policies.

    What: validates the command, the unique policy keys and the scenario revision against one store snapshot, then simulates each policy and returns the run snapshots, or a rejected invalid_input Result.
    When called: by RescueCentral.compare in rescue/application/central.py.
    Why: every policy must run on the same scenario revision, and the simulation runs after the store snapshot so no store lock is held during it.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    try:
        if not isinstance(command, ComparePolicies):
            raise DomainValidationError("compare requires a ComparePolicies command")
        scenario_id = normalize_id(command.scenario_id)
        scenario_revision = normalize_positive_quantity(command.scenario_revision)
        if not isinstance(command.policy_keys, (tuple, list)) or not command.policy_keys:
            raise DomainValidationError("comparison requires at least one policy key")

        policy_keys: list[tuple[str, int]] = []
        for key in command.policy_keys:
            if not isinstance(key, (tuple, list)) or len(key) != 2:
                raise DomainValidationError("policy keys require an ID and revision")
            normalized_key = (
                normalize_id(key[0]),
                normalize_positive_quantity(key[1]),
            )
            if normalized_key in policy_keys:
                raise DomainValidationError("policy keys must be unique")
            policy_keys.append(normalized_key)

        state = store.snapshot()
        scenario = next(
            (
                item
                for item in state.scenarios
                if item.scenario_id == scenario_id and item.revision == scenario_revision
            ),
            None,
        )
        if scenario is None:
            raise DomainValidationError("unknown scenario revision")

        policies = []
        for policy_id, revision in policy_keys:
            policy = next(
                (
                    item
                    for item in state.policies
                    if item.policy_id == policy_id and item.revision == revision
                ),
                None,
            )
            if policy is None:
                raise DomainValidationError("unknown policy revision")
            policies.append(policy)
    except DomainValidationError, TypeError:
        return make_result("rejected", reason="invalid_input")

    try:
        snapshots = tuple(
            simulator.simulate(scenario, policy, id_source.next_id("simulation"))
            for policy in policies
        )
    except DomainValidationError, TypeError:
        return make_result("rejected", reason="invalid_input")
    return make_result("applied", snapshots)
