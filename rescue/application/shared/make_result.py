"""Build the Result every service returns.

What: returns a Result with the given status, value and reason.
When called: by every service for each command outcome.
Why: one builder keeps the outcome shape the same across services.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from rescue.application.contracts import Result


def make_result(status: str, value=None, reason: str | None = None) -> Result:
    """Make result.

    What: builds a Result from a status, an optional value and an optional reason.
    When called: by every application service and shared helper that returns a Result.
    Why: one place builds results so services share the same shape.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    return Result(status=status, value=value, reason=reason)
