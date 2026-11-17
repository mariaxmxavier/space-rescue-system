"""In-memory ``TransactionStore`` with optimistic commit.

What: keeps one run's ``RunState`` and a version number; operations run against a snapshot in
parallel and publish with a compare-and-swap on the version.

When: built by ``rescue.bootstrap.new_run`` for every new run and shared by its concurrent callers.

Why: no caller waits for another caller's work. Only the publish step is serial, and it is short,
so requests that arrive at the same time are processed in parallel, and a conflict is detected
rather than prevented by a lock held for the whole operation.
"""

from __future__ import annotations

from collections.abc import Callable
from threading import Lock

from rescue.adapters.ports.transaction_store import TransactionStore
from rescue.state import RunState


class MemoryTransactionStore(TransactionStore):
    """Optimistic in-memory store: parallel operations, serial compare-and-publish.

    What: implements ``TransactionStore`` with a published ``RunState``, its version and a short
    guard lock held only to read or swap them.

    When: one instance per run, shared by every concurrent use case of that run.

    Why: an operation may run while another one publishes, so readers and writers never queue
    behind a long operation; a writer whose snapshot went stale runs again on the newer state.
    """

    def __init__(self, initial_state: RunState) -> None:
        """Hold ``initial_state`` as the published state at version zero.

        What: stores the starting state, its version and the guard lock.

        When: called once by ``rescue.bootstrap.new_run``.

        Why: rejects a wrong type up front, so no transaction ever starts from invalid state.
        """
        if not isinstance(initial_state, RunState):
            raise TypeError("initial_state must be a RunState")
        self._state = initial_state
        self._version = 0
        self._guard = Lock()

    def transact[T](self, operation: Callable[[RunState], tuple[RunState, T]]) -> T:
        """Run ``operation`` on a snapshot and publish its state if no other commit came first.

        What: reads the published state and its version, runs ``operation`` without any lock, then
        publishes the staged state only if the version is unchanged. On a conflict it runs again on
        the newer state. A read-only operation, which returns the state it was given, publishes
        nothing.

        When: called by every use case that reads or changes run state, including from several
        threads at once.

        Why: each retry means another transaction committed, so the system as a whole always makes
        progress; the version check keeps a stale result from overwriting a newer one.
        """
        while True:
            with self._guard:
                base, version = self._state, self._version
            staged_state, result = operation(base)
            if not isinstance(staged_state, RunState):
                raise TypeError("transaction must return a RunState")
            if staged_state is base:
                return result
            with self._guard:
                if self._version == version:
                    self._state = staged_state
                    self._version = version + 1
                    return result
