"""CommitmentSource interface of the Inventory category.

When: passed to `usage` and `hold_quote` as the run's missions.
Why: the market counts every mission's commitments without knowing the mission type.
Diagram: ShipMarket class-diagram.mmd `CommitmentSource` (realised by MissionOperations `Mission`).
"""

from __future__ import annotations

from typing import Protocol

from rescue.market.models.inventory.commitment_request import CommitmentRequest
from rescue.values import Id


class CommitmentSource(Protocol):
    """Something with a unique `mission_id` and the seat requests it has made.

    When: any object with these read-only attributes fits (a Mission does).
    Why: each mission must be counted once; `usage` refuses duplicated mission ids.
    Diagrams: ShipMarket class-diagram.mmd and entity-relationship-diagram.mmd.
    """

    @property
    def mission_id(self) -> Id: ...

    @property
    def requests(self) -> tuple[CommitmentRequest, ...]: ...
