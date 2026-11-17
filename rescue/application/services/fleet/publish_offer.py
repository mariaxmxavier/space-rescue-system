"""Publish a ship offer revision for a mission.

What: adds the revision to the ship's offer, reports a replay of a known revision, and rejects the rest with a reason.
When called: by RescueCentral.publish_offer, which hands the PublishOffer command to this service.
Why: a ship states what it can carry one revision at a time, and a refused revision must change nothing.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.adapters.ports import TransactionStore
from rescue.application.contracts import PublishOffer, Result
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.find_mission import find_mission
from rescue.application.shared.make_result import make_result
from rescue.market.models.offers import ShipOfferRevision
from rescue.market.models.offers.rules import publish_offer_revision
from rescue.state import RunState
from rescue.values import DomainValidationError, normalize_id


def publish_offer(command: PublishOffer, *, store: TransactionStore) -> Result:
    """Publish an offer revision for a ship and mission.

    What: Check the mission, the ship, the revision type and the offer identity, answer replayed for a known identical revision, reject a conflicting one, otherwise add the revision to the market.
    When called: RescueCentral.publish_offer in rescue/application/central.py.
    Why: A ship states what it can carry one revision at a time, and a refused revision must change nothing. Revision ids are immutable: the same revision may be replayed, a different one under the same id is a revision_conflict.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def operation(state: RunState):
        """Transaction step of publish_offer.

        What: applies the publish_offer rule to the state it receives and returns the new state with its Result.
        When called: passed to store.transact by publish_offer, which runs it once per call.
        Why: Revision ids are immutable: the same revision may be replayed, a different one under the same id is a revision_conflict.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        try:
            mission_id = normalize_id(command.mission_id)
            ship_id = normalize_id(command.ship_id)
            offer_id = normalize_id(command.offer_id)
            if find_mission(state, mission_id) is None:
                return state, make_result("rejected", reason="unknown_mission")
            if not any(item.ship_id == ship_id for item in state.market.ships):
                return state, make_result("rejected", reason="unknown_ship")
            revision = command.revision
            if not isinstance(revision, ShipOfferRevision):
                raise DomainValidationError("revision must be a ShipOfferRevision")
            existing_offer = next(
                (item for item in state.market.offers if item.offer_id == offer_id),
                None,
            )
            if existing_offer is not None and (
                existing_offer.mission_id != mission_id or existing_offer.ship_id != ship_id
            ):
                return state, make_result("rejected", reason="identity_conflict")
            for offer in state.market.offers:
                for existing in offer.revisions:
                    if existing.revision_id == revision.revision_id:
                        if offer.offer_id == offer_id and existing == revision:
                            return state, make_result("replayed", offer)
                        return state, make_result("rejected", reason="revision_conflict")
            market = publish_offer_revision(
                state.market,
                offer_id,
                revision,
                mission_id=mission_id,
                ship_id=ship_id,
            )
            snapshot = next(item for item in market.offers if item.offer_id == offer_id)
            return replace(state, market=market), make_result("applied", snapshot)
        except (DomainValidationError, TypeError) as error:
            return state, make_result("rejected", reason=error_reason_for(error))

    return store.transact(operation)
