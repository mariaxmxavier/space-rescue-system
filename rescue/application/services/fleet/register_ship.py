"""Register a rescue ship in the run's market.

What: adds the ship to the market, or rejects it when its identity is taken or its values are invalid.
When called: by RescueCentral.register_ship, which hands the RegisterShip command to this service.
Why: a ship must be known before it can publish availability or offers.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.adapters.ports import TransactionStore
from rescue.application.contracts import RegisterShip, Result
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.make_result import make_result
from rescue.market.models.fleet import Ship
from rescue.state import RunState
from rescue.values import DomainValidationError


def register_ship(command: RegisterShip, *, store: TransactionStore) -> Result:
    """Add a ship to the market, or reject it when its identity is taken or its values are invalid.

    What: Build the Ship, reject a taken ship id as identity_conflict, otherwise append it to the market of the state.
    When called: RescueCentral.register_ship in rescue/application/central.py.
    Why: A ship must be known before it can publish availability or offers. The identity check keeps a ship id unique within a run.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def operation(state: RunState):
        """Transaction step of register_ship.

        What: applies the register_ship rule to the state it receives and returns the new state with its Result.
        When called: passed to store.transact by register_ship, which runs it once per call.
        Why: The identity check keeps a ship id unique within a run.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        try:
            ship = Ship(command.ship_id, command.name)
            if any(item.ship_id == ship.ship_id for item in state.market.ships):
                return state, make_result("rejected", reason="identity_conflict")
            market = replace(state.market, ships=(*state.market.ships, ship))
            return replace(state, market=market), make_result("applied", ship)
        except (DomainValidationError, TypeError) as error:
            return state, make_result("rejected", reason=error_reason_for(error))

    return store.transact(operation)
