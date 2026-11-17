"""Read one recorded mobilisation decision.

What: returns the decision with this id, or rejects with unknown_decision.
When called: by RescueCentral.get_decision.
Why: callers can read back the basis of a decision that a request later cites.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from rescue.adapters.ports import TransactionStore
from rescue.application.contracts import DecisionSnapshot, Result
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.make_result import make_result
from rescue.mobilisation.models import MobilisationDecision
from rescue.state import RunState
from rescue.values import DomainValidationError, normalize_id


def get_decision(decision_id: str, *, store: TransactionStore) -> Result[DecisionSnapshot]:
    """Get decision.

    What: returns the MobilisationDecision with the normalised id from the decision index as an applied Result, or rejects with unknown_decision or the reason for an invalid id.
    When called: by RescueCentral.get_decision in rescue/application/central.py.
    Why: a request cites a decision by id, so a caller must be able to read back the basis it was made on.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def operation(state: RunState):
        try:
            normalized = normalize_id(decision_id)
            decision = next(
                (
                    item
                    for item in state.decision_index
                    if isinstance(item, MobilisationDecision) and item.decision_id == normalized
                ),
                None,
            )
            if decision is None:
                return state, make_result("rejected", reason="unknown_decision")
            return state, make_result("applied", decision)
        except (DomainValidationError, TypeError) as error:
            return state, make_result("rejected", reason=error_reason_for(error))

    return store.transact(operation)
