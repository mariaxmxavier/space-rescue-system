"""The ``TransactionStore`` port: atomic access to the state of one application run.

What: declares how the application reads and changes the run state.

When: every use case in ``RescueCentral`` and the experiment runner goes through it to read or
change state.

Why: the application must change state all-or-nothing and must not know where the state lives.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from rescue.application.state import RunState


class TransactionStore(ABC):
    """Atomic store of one run's ``RunState``.

    What: runs an operation against the current state and publishes the result only on success.

    When: built once per run by ``rescue.bootstrap.new_run`` and injected into ``RescueCentral``.

    Why: readers must never see a half-applied change, whatever the storage behind it.
    """

    @abstractmethod
    def transact[T](self, operation: Callable[[RunState], tuple[RunState, T]]) -> T:
        """Apply ``operation`` atomically and return its result.

        What: passes the current state to ``operation``, which returns ``(new_state, result)``;
        publishes ``new_state`` and returns ``result``. If ``operation`` raises or does not return
        a ``RunState``, nothing is published. ``operation`` may run more than once, on a newer state
        after a conflicting commit, so it must have no effect beyond drawing unique IDs.

        When: called by each use case that reads or changes run state.

        Why: one operation is one transaction, so concurrent callers cannot interleave partial
        changes.
        """

    def snapshot(self) -> RunState:
        """Return the whole published state as it is now.

        What: reads the current state through ``transact`` without changing it.

        When: called when a caller needs a consistent view of all state at once, e.g. before an
        experiment run or a final report.

        Why: declared on the port so callers never depend on a method only one adapter has; built
        on ``transact`` so every store gets the same consistency for free.
        """
        return self.transact(lambda state: (state, state))
