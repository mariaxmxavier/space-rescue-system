"""In-memory contexts and call histories for local HTTP runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock

from rescue.bootstrap import RunContext, new_run


@dataclass(frozen=True, slots=True)
class CallEntry:
    """One completed request and its complete HTTP outcome."""

    sequence: int
    method: str
    path: str
    input: object
    status_code: int
    response: object


@dataclass(slots=True)
class RunRecord:
    """A run context with serialized requests and its in-memory call history."""

    context: RunContext
    lock: RLock = field(default_factory=RLock)
    history: list[CallEntry] = field(default_factory=list)

    def append(
        self, method: str, path: str, input: object, status_code: int, response: object
    ) -> CallEntry:
        entry = CallEntry(len(self.history) + 1, method, path, input, status_code, response)
        self.history.append(entry)
        return entry


class RunRegistry:
    """Own isolated in-memory runs for one API process."""

    def __init__(self) -> None:
        self._runs: dict[str, RunRecord] = {}
        self._lock = RLock()

    def create(self, run_id: str, central_id: str, *, policies=(), scenarios=()) -> RunRecord:
        with self._lock:
            if run_id in self._runs:
                raise ValueError(f"run already exists: {run_id}")
            record = RunRecord(
                new_run(run_id, central_id, policies=tuple(policies), scenarios=tuple(scenarios))
            )
            self._runs[run_id] = record
            return record

    def get(self, run_id: str) -> RunRecord | None:
        with self._lock:
            return self._runs.get(run_id)
