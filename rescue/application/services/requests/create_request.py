"""Create a pending seat request for a ship on a mission.

What: runs open_request inside one transaction, so a refusal leaves the run unchanged.
When called: by RescueCentral.create_request, which hands it the command, the store and the id source.
Why: a request commits seats of one ship to one mission, and a repeated command must replay.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from rescue.adapters.ports import IdSource, TransactionStore
from rescue.application.contracts import CreateRequest, Result
from rescue.application.contracts.snapshots import RequestSnapshot
from rescue.application.shared.open_request import open_request


def create_request(
    command: CreateRequest, *, store: TransactionStore, id_source: IdSource
) -> Result[RequestSnapshot]:
    """Open a pending seat request inside one store transaction.

    What: hands the command fields to open_request in one transaction, so a refusal leaves the run state unchanged.
    When called: by RescueCentral.create_request in rescue/application/central.py.
    Why: a request commits seats of one ship to one mission, and a repeated command id must replay its first result.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    return store.transact(
        lambda state: open_request(
            state,
            id_source=id_source,
            command_id=command.command_id,
            mission_id=command.mission_id,
            ship_id=command.ship_id,
            requested_seats=command.requested_seats,
            revision_id=command.revision_id,
            now=command.now,
            response_deadline=command.response_deadline,
            decision_id=command.decision_id,
        )
    )
