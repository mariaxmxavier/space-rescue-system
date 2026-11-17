"""Publish the availability of a ship.

What: adds the availability to the market, reports a replay when nothing changes, and rejects invalid values.
When called: by RescueCentral.publish_availability, which hands the PublishAvailability command to this service.
Why: quoting and mobilisation read the published availability of the fleet.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.adapters.ports import TransactionStore
from rescue.application.contracts import PublishAvailability, Result
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.make_result import make_result
from rescue.market.models.availability import ShipAvailability
from rescue.market.models.availability.rules import publish_availability as publish_to_market
from rescue.state import RunState
from rescue.values import DomainValidationError


def publish_availability(command: PublishAvailability, *, store: TransactionStore) -> Result:
    """Publish an availability for a ship; report a replay when the market does not change.

    What: Check the value is a ShipAvailability, publish it to the market, and answer replayed when the market is equal to the old one, applied otherwise.
    When called: RescueCentral.publish_availability in rescue/application/central.py.
    Why: Quoting and mobilisation read the published availability of the fleet. A repeated publication must be harmless, so it is reported as a replay and changes nothing.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def operation(state: RunState):
        """Transaction step of publish_availability.

        What: applies the publish_availability rule to the state it receives and returns the new state with its Result.
        When called: passed to store.transact by publish_availability, which runs it once per call.
        Why: A repeated publication must be harmless, so it is reported as a replay and changes nothing.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        try:
            if not isinstance(command.availability, ShipAvailability):
                raise DomainValidationError("availability must be a ShipAvailability value")
            market = publish_to_market(state.market, command.availability)
            if market == state.market:
                status = "replayed"
            else:
                status = "applied"
            return replace(state, market=market), make_result(status, command.availability)
        except (DomainValidationError, TypeError) as error:
            return state, make_result("rejected", reason=error_reason_for(error))

    return store.transact(operation)
