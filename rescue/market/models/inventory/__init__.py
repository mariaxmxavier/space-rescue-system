"""Inventory category: how full a ship is.

When: read before every hold and whenever progress or a policy needs a ship's free seats.
Why: holds live in the market but pending and confirmed seats live in missions; inventory adds
them up once, through an interface the market owns.
Diagram: ShipMarket class-diagram.mmd, namespace Inventory.

Import entities as `from rescue.market.models.inventory import CommitmentRequest` and rules from
`rescue.market.models.inventory.rules`.
"""

from rescue.market.models.inventory.commitment_request import CommitmentRequest
from rescue.market.models.inventory.commitment_source import CommitmentSource
from rescue.market.models.inventory.ship_usage import ShipUsage

__all__ = ["CommitmentRequest", "CommitmentSource", "ShipUsage"]
