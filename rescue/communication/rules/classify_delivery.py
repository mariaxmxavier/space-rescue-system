"""Classify one inbound ship response delivery from primitive facts.

What: maps DeliveryFacts to the DeliveryDecision that says what to record, do and report.
When called: RescueCentral.record_response calls it for every ship response, first and before the
  session step (accept_inbound).
Why: one pure first-match table keeps every delivery outcome explainable and independent of storage.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from rescue.communication.models.deliveries.delivery_decision import DeliveryDecision
from rescue.communication.models.deliveries.delivery_facts import DeliveryFacts
from rescue.communication.models.vocabulary.delivery_disposition import DeliveryDisposition
from rescue.communication.models.vocabulary.delivery_reason import DeliveryReason


def _record(
    disposition: DeliveryDisposition,
    reason: DeliveryReason,
    status: str,
    result_reason: str | None,
    action: str = "record",
) -> DeliveryDecision:
    """What: builds one DeliveryDecision from a precedence row's outcome fields.
    Why: keeps each row of the classification table a single named call, so the precedence reads as a list.
    """
    return DeliveryDecision(disposition, reason, action, status, result_reason)


def classify_delivery(facts: DeliveryFacts) -> DeliveryDecision:
    """Return the decision for one delivery; the first matching row wins.

    What: tests the rows in this order and returns at the first match: known identical delivery
      (ignored, nothing recorded), known different delivery (identity_conflict, nothing recorded),
      message conflict, unknown request (lost without receipt, otherwise unknown_request),
      send before submission, no receipt (lost), closed request (late when expired and received
      at or after the deadline, otherwise closed_request), open request received at or after
      its deadline (expire then record late), and otherwise apply.
    When called: once per delivery, first in RescueCentral.record_response, before the session
      step (accept_inbound) and the mission rule.
    Why: the order matches the former response handling, so a later row never overrides an
      earlier one; a failing mission rule is decided by central, not here.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """
    rejected = DeliveryDisposition.REJECTED
    received = facts.received_at is not None
    past_deadline = received and facts.deadline is not None and facts.received_at >= facts.deadline
    if facts.delivery_known:
        if facts.delivery_identical:
            return DeliveryDecision(None, None, "none", "ignored", None)
        return DeliveryDecision(None, None, "none", "rejected", "identity_conflict")
    if facts.message_conflicts:
        return _record(rejected, DeliveryReason.IDENTITY_CONFLICT, "rejected", "identity_conflict")
    if not facts.request_known:
        if not received:
            return _record(DeliveryDisposition.LOST, DeliveryReason.TRANSPORT_LOSS, "applied", None)
        return _record(
            DeliveryDisposition.IGNORED,
            DeliveryReason.UNKNOWN_REQUEST,
            "ignored",
            "unknown_request",
        )
    if facts.submitted_at is not None and facts.sent_at < facts.submitted_at:
        return _record(rejected, DeliveryReason.INVALID_INPUT, "rejected", "invalid_input")
    if not received:
        return _record(DeliveryDisposition.LOST, DeliveryReason.TRANSPORT_LOSS, "applied", None)
    late = (DeliveryDisposition.LATE, DeliveryReason.DEADLINE_EXPIRED, "ignored", "late")
    if not facts.request_open:
        if facts.request_expired and past_deadline:
            return _record(*late)
        return _record(
            DeliveryDisposition.IGNORED,
            DeliveryReason.CLOSED_REQUEST,
            "ignored",
            "closed_request",
        )
    if past_deadline:
        return _record(*late, action="expire_then_record")
    return _record(
        DeliveryDisposition.APPLIED, DeliveryReason.RESPONSE_APPLIED, "applied", None, "apply"
    )
