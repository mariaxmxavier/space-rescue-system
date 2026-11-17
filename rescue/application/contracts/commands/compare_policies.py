"""The ComparePolicies command contract.

What: defines the command that compares policies on one scenario revision.
When called: imported by RescueCentral.compare, the compare_policies service and callers that build the command.
Why: a command is one frozen value, so a service receives its input already shaped and unchangeable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import Id


@dataclass(frozen=True, slots=True)
class ComparePolicies:
    """Ask central to compare several policies on one scenario.

    What: names the scenario, its revision and the (policy id, revision) keys to compare.
    When called: by RescueCentral.compare, which hands the command to the compare_policies service.
    Why: experiments need every policy run on the same scenario to compare outcomes.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    scenario_id: Id
    scenario_revision: int
    policy_keys: tuple[tuple[Id, int], ...]
