"""CommitmentRequest interface of the Inventory category.

When: read by `usage` for every request of every mission.
Why: the market needs only these four facts about a seat request; naming them here means the
market never imports the mission package (contract `market-standalone`).
Diagram: ShipMarket class-diagram.mmd `CommitmentRequest` (realised by MissionOperations `SeatRequest`).
"""

from __future__ import annotations

from typing import Protocol

from rescue.values import Id


class CommitmentRequest(Protocol):
    """A seat request as the market sees it: which ship, how many seats, and its outcome.

    When: any object with these read-only attributes fits (a mission's SeatRequest does).
    Why: "pending" requests count `requested_seats`; "accepted" and "partially_accepted" count
    `confirmed_seats`; any other outcome counts nothing.
    Diagrams: ShipMarket class-diagram.mmd and entity-relationship-diagram.mmd.
    """

    @property
    def ship_id(self) -> Id: ...

    @property
    def requested_seats(self) -> int: ...

    @property
    def confirmed_seats(self) -> int: ...

    @property
    def outcome(self) -> str: ...
