"""The Mobilise command contract.

What: defines the command that mobilises ships for a mission under a policy.
When called: imported by RescueCentral.mobilise, the mobilise service and callers that build the command.
Why: a command is one frozen value, so a service receives its input already shaped and unchangeable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import Id, Instant


@dataclass(frozen=True, slots=True)
class Mobilise:
    """Ask central to mobilise ships for a mission under a policy.

    What: names the mission, the policy and its revision and the current instant.
    When called: by RescueCentral.mobilise, which hands the command to the mobilise service.
    Why: the policy decides which ships and seats are committed to the mission.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    mission_id: Id
    policy_id: Id
    policy_revision: int
    now: Instant
