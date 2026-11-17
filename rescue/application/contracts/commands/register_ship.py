"""The RegisterShip command contract.

What: defines the command that registers a rescue ship.
When called: imported by RescueCentral.register_ship, the register_ship service and callers that build the command.
Why: a command is one frozen value, so a service receives its input already shaped and unchangeable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import Id


@dataclass(frozen=True, slots=True)
class RegisterShip:
    """Ask central to register a rescue ship.

    What: names the ship and gives its display name.
    When called: by RescueCentral.register_ship, which hands the command to the register_ship service.
    Why: a ship must be known before it can publish availability or offers.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    ship_id: Id
    name: str
