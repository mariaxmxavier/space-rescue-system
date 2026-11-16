"""Ports used by application orchestration and outer adapters."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, TypeVar

from rescue.application.state import RunState
from rescue.values import Id, Instant

T = TypeVar("T")


class TransactionStore(Protocol):
    """Run-local atomic state boundary."""

    def transact(self, operation: Callable[[RunState], tuple[RunState, T]]) -> T:
        """Run an operation against a snapshot and publish only on success."""


class Clock(Protocol):
    """Source of operation time when a caller has not supplied one."""

    def now(self) -> Instant: ...


class IdSource(Protocol):
    """Source of unique IDs scoped to one application run."""

    def next_id(self, kind: str) -> Id: ...
