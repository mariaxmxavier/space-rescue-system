"""The value every application command returns.

What: a frozen record of a status, an optional value and an optional reason.
When called: built by every service for each command, and read by transports and the demo.
Why: one transport-neutral result shape lets callers handle all commands the same way; the
  constructor refuses an unknown status or reason.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from rescue.application.contracts.error_reason import ErrorReason
from rescue.application.contracts.result_status import ResultStatus

_T = TypeVar("_T")


@dataclass(frozen=True, slots=True)
class Result(Generic[_T]):
    """The outcome of one command.

    What: holds a status, an optional value and an optional reason.
    When called: returned by every RescueCentral method and built by every service.
    Why: callers handle every command through one shape; the constructor refuses an unknown status or reason.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    status: str
    value: _T | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        """Refuse a status or reason outside the closed sets.

        What: checks status against ResultStatus and a present reason against ErrorReason, raising ValueError.
        When called: automatically on every Result construction.
        Why: keeps the outcome of a command a checkable value.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        if self.status not in {status.value for status in ResultStatus}:
            raise ValueError(f"unknown result status: {self.status!r}")
        if self.reason is not None and self.reason not in {reason.value for reason in ErrorReason}:
            raise ValueError(f"unknown result reason: {self.reason!r}")
