"""The PublishOffer command contract.

What: defines the command that publishes a ship offer revision.
When called: imported by RescueCentral.publish_offer, the publish_offer service and callers that build the command.
Why: a command is one frozen value, so a service receives its input already shaped and unchangeable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rescue.values import Id

if TYPE_CHECKING:
    from rescue.market.models.offers import ShipOfferRevision


@dataclass(frozen=True, slots=True)
class PublishOffer:
    """Ask central to publish a ship offer revision for a mission.

    What: names the offer, mission and ship and carries the offer revision.
    When called: by RescueCentral.publish_offer, which hands the command to the publish_offer service.
    Why: a ship states what it can carry and on what terms, one revision at a time.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    offer_id: Id
    mission_id: Id
    ship_id: Id
    revision: ShipOfferRevision
