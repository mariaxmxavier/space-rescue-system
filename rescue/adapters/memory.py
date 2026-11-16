"""Single-lock in-memory adapter with atomic staged state publication."""

from __future__ import annotations

from collections.abc import Callable
from threading import Lock
from typing import TypeVar

from rescue.application.state import RunState

T = TypeVar("T")


class MemoryTransactionStore:
    def __init__(self, initial_state: RunState) -> None:
        if not isinstance(initial_state, RunState):
            raise TypeError("initial_state must be a RunState")
        self._state = initial_state
        self._lock = Lock()

    def transact(self, operation: Callable[[RunState], tuple[RunState, T]]) -> T:
        with self._lock:
            staged_state, result = operation(self._state)
            if not isinstance(staged_state, RunState):
                raise TypeError("transaction must return a RunState")
            self._state = staged_state
            return result

    def snapshot(self) -> RunState:
        return self.transact(lambda state: (state, state))
