"""Record one ship response delivery and apply it to the request when the rules allow.

What: normalises the command, classifies the delivery, resolves the session, then publishes the delivery as ignored, recorded, expired-then-recorded or applied.
When called: by RescueCentral.record_response, once per inbound ship response attempt, including lost and repeated ones.
Why: classification and sequencing live in the communication rules; this orchestrator only sequences the delivery steps inside one transaction and draws one event id per mission change.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
"""

from __future__ import annotations

from rescue.adapters.ports import IdSource, TransactionStore
from rescue.application.contracts import RecordResponse, RequestSnapshot, Result
from rescue.application.shared.delivery.classify_response import classify_response
from rescue.application.shared.delivery.normalise_response import normalise_response
from rescue.application.shared.delivery.publish_delivery import publish_delivery
from rescue.application.shared.delivery.resolve_session import resolve_session
from rescue.application.shared.error_reason_for import error_reason_for
from rescue.application.shared.make_result import make_result
from rescue.application.shared.replace_mission import replace_mission
from rescue.mission import rules as mission_rules
from rescue.mission.models import RequestOutcome
from rescue.state import RunState
from rescue.values import DomainValidationError, TransitionContext


def record_response(
    command: RecordResponse, *, store: TransactionStore, id_source: IdSource
) -> Result[RequestSnapshot]:
    """Record one ship response delivery and apply it to its request when the rules allow.

    What: inside one transaction it normalises the command, classifies the delivery, resolves the session and then publishes it as ignored, recorded, expired-then-recorded or applied, drawing one event id per mission change; any validation error becomes a rejection.
    When called: by RescueCentral.record_response in rescue/application/central.py.
    Why: classification and sequencing belong to the communication rules, so this function only orders the steps and keeps the whole delivery atomic.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
    """

    def operation(state: RunState):
        try:
            normalised = normalise_response(command)
            context, decision = classify_response(state, normalised)
            request = context.request
            value = None if decision.result_status == "rejected" else request
            outcome = make_result(decision.result_status, value, decision.result_reason)
            if decision.action == "none":
                return state, outcome
            context, stale = resolve_session(state, context, command)
            if stale is not None:
                return state, stale
            mission = context.mission
            request_id = context.request_id
            keep_message = not context.message_conflicts
            if context.verdict == "duplicate":
                return (
                    publish_delivery(
                        state,
                        context,
                        "ignored",
                        "duplicate_sequence",
                        keep_message=keep_message,
                        report=False,
                    ),
                    make_result("ignored", request, "duplicate_sequence"),
                )
            if decision.action == "record":
                return (
                    publish_delivery(
                        state,
                        context,
                        decision.disposition,
                        decision.reason,
                        keep_message=keep_message,
                    ),
                    outcome,
                )
            if decision.action == "expire_then_record":
                expired = mission_rules.apply_outcome(
                    mission,
                    request_id,
                    RequestOutcome.EXPIRED,
                    0,
                    TransitionContext(
                        id_source.next_id("event"),
                        context.received_at,
                        "response_deadline_reached",
                        context.message_id,
                    ),
                )
                expired_request = next(
                    item for item in expired.requests if item.request_id == request_id
                )
                updated = publish_delivery(
                    replace_mission(state, expired),
                    context,
                    decision.disposition,
                    decision.reason,
                    decided_mission=expired,
                )
                return updated, make_result(
                    decision.result_status, expired_request, decision.result_reason
                )
            try:
                updated_mission = mission_rules.apply_outcome(
                    mission,
                    request_id,
                    command.outcome,
                    context.confirmed,
                    TransitionContext(
                        id_source.next_id("event"),
                        context.received_at,
                        command.outcome,
                        context.message_id,
                    ),
                )
            except (DomainValidationError, TypeError) as error:
                reason = error_reason_for(error)
                return publish_delivery(state, context, "rejected", reason), make_result(
                    "rejected", reason=reason
                )
            updated = publish_delivery(
                replace_mission(state, updated_mission),
                context,
                decision.disposition,
                decision.reason,
                decided_mission=updated_mission,
            )
            applied_request = next(
                item for item in updated_mission.requests if item.request_id == request_id
            )
            return updated, make_result("applied", applied_request)
        except (DomainValidationError, TypeError) as error:
            return state, make_result("rejected", reason=error_reason_for(error))

    return store.transact(operation)
