"""The PublishAvailability command contract.

What: defines the command that publishes a ship availability.
When called: imported by RescueCentral.publish_availability, the publish_availability service and callers that build the command.
Why: a command is one frozen value, so a service receives its input already shaped and unchangeable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rescue.market.models.availability import ShipAvailability


@dataclass(frozen=True, slots=True)
class PublishAvailability:
    """Ask central to publish the availability of a ship.

    What: carries one ShipAvailability value.
    When called: by RescueCentral.publish_availability, which hands the command to the publish_availability service.
    Why: quoting and mobilisation read the published availability of the fleet.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    availability: ShipAvailability
