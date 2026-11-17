"""Mobilise ships for a mission under a policy.

What: scores each offer on the mission against the policy and records the resulting decision.
When called: by RescueCentral.mobilise.
Why: a mobilisation decision is a proposal that reserves no capacity, kept so a request can cite it.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.adapters.ports import IdSource, TransactionStore
from rescue.application.contracts import DecisionSnapshot, Mobilise, Result
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.find_mission import find_mission
from rescue.application.shared.make_result import make_result
from rescue.market.models.inventory.rules import usage
from rescue.mission.models import RequestOutcome
from rescue.mobilisation.models import Candidate, DecisionContext, MobilisationPolicy
from rescue.mobilisation.services.decide import select_offers
from rescue.state import RunState
from rescue.values import (
    DomainValidationError,
    normalize_id,
    normalize_instant,
    normalize_positive_quantity,
)


def mobilise(
    command: Mobilise, *, store: TransactionStore, id_source: IdSource
) -> Result[DecisionSnapshot]:
    """Mobilise.

    What: normalises the command, finds the mission and the policy revision, builds one Candidate per mission offer with the seats free on the ship and on the offer revision, selects offers with select_offers and stores the decision in the decision index.
    When called: by RescueCentral.mobilise in rescue/application/central.py.
    Why: a decision is a proposal that reserves no capacity, so free seats are counted from pending and confirmed requests and only the decision index changes.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def operation(state: RunState):
        try:
            mission_id = normalize_id(command.mission_id)
            policy_id = normalize_id(command.policy_id)
            policy_revision = normalize_positive_quantity(command.policy_revision)
            instant = normalize_instant(command.now)
            mission = find_mission(state, mission_id)
            if mission is None:
                return state, make_result("rejected", reason="unknown_mission")
            policy = next(
                (
                    value
                    for value in state.policies
                    if isinstance(value, MobilisationPolicy)
                    and value.policy_id == policy_id
                    and value.revision == policy_revision
                ),
                None,
            )
            if policy is None:
                return state, make_result("rejected", reason="invalid_input")

            offers = tuple(offer for offer in state.market.offers if offer.mission_id == mission_id)
            candidates: list[Candidate] = []
            for offer in sorted(offers, key=lambda item: item.ship_id):
                revision = offer.current_revision
                inventory = usage(state.market, state.missions, offer.ship_id)
                revision_used = sum(
                    request.requested_seats
                    if request.outcome == RequestOutcome.PENDING
                    else request.confirmed_seats
                    for current_mission in state.missions
                    for request in current_mission.requests
                    if request.revision_id == revision.revision_id
                    and request.outcome
                    in {
                        RequestOutcome.PENDING,
                        RequestOutcome.ACCEPTED,
                        RequestOutcome.PARTIALLY_ACCEPTED,
                    }
                )
                free_for_revision = max(0, revision.capacity - revision_used)
                candidates.append(
                    Candidate(
                        revision=revision,
                        free_seats=min(inventory.free, free_for_revision),
                        ship_id=offer.ship_id,
                    )
                )
            decision = select_offers(
                mission,
                tuple(candidates),
                policy,
                DecisionContext(
                    decision_id=id_source.next_id("decision"),
                    recorded_at=instant,
                    evaluation_ids=tuple(id_source.next_id("evaluation") for _ in candidates),
                ),
            )
            updated_state = replace(state, decision_index=(*state.decision_index, decision))
            return updated_state, make_result("applied", decision)
        except (DomainValidationError, TypeError) as error:
            return state, make_result("rejected", reason=error_reason_for(error))

    return store.transact(operation)
