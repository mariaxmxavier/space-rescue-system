"""Map a domain error to a stable reason code.

What: returns the first reason whose keywords appear in the error message, else invalid_input.
When called: by every service that turns a raised domain error into a rejected Result.
Why: callers see reason codes, never raw domain messages.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations


def error_reason_for(error: Exception) -> str:
    """Error reason for.

    What: maps the message of a domain error to one stable rejection reason, with invalid_input as the fallback.
    When called: by every service that turns DomainValidationError or TypeError into a rejected Result, for example mobilise, open_request and record_response.
    Why: callers get a small closed set of reason codes rather than free text messages.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    message = str(error).casefold()
    if "unknown mission" in message or "mission" in message and "unknown" in message:
        return "unknown_mission"
    if "unknown ship" in message or "ship" in message and "unknown" in message:
        return "unknown_ship"
    if "unknown request" in message or "request" in message and "unknown" in message:
        return "unknown_request"
    if "demand" in message:
        return "insufficient_demand"
    if "capacity" in message or "shortfall" in message:
        return "insufficient_capacity"
    if "unavailable" in message:
        return "unavailable"
    if "expired" in message or "expiry" in message:
        return "expired_quote"
    if "revision" in message:
        return "revision_conflict"
    if "closed" in message or "terminal" in message:
        return "closed_request"
    return "invalid_input"
