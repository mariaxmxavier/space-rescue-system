"""Shared fakes for the application service unit tests.

What: in-memory stand-ins for the transaction store, id source and simulator ports, plus an empty run state.
When called: imported by every service test that needs a port without wiring a real run.
Why: service tests stay unit tests, fast and deterministic, and can see what a service published or asked for.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from collections import Counter

from rescue.adapters.ports.id_source import IdSource
from rescue.adapters.ports.simulator import Simulator
from rescue.adapters.ports.transaction_store import TransactionStore
from rescue.market.models.b3_market import B3Market
from rescue.state import RunState


def empty_state() -> RunState:
    """Build a run state with no missions, sessions or history.

    What: RunState("run-1", "central-1", B3Market("market-1")).
    When called: by tests as the starting state of a FakeStore.
    Why: one agreed starting point keeps service tests comparable.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    return RunState("run-1", "central-1", B3Market("market-1"))


class FakeStore(TransactionStore):
    """Transaction store holding one RunState in memory.

    What: publishes the operation's new state only when the operation returns without raising.
    When called: injected into a service under test.
    Why: tests check that a rejected operation leaves the state untouched.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def __init__(self, state: RunState) -> None:
        self.state = state

    def transact[T](self, operation):
        """Run the operation and publish its state on success.

        What: returns the operation's result; leaves the state unchanged if it raises.
        When called: by each service under test.
        Why: mirrors the port's all-or-nothing contract.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        new_state, result = operation(self.state)
        self.state = new_state
        return result


class FakeIds(IdSource):
    """Id source with one counter per kind.

    What: returns "<kind>-<n>", counting from 1 for each kind.
    When called: injected into a service under test that draws ids.
    Why: predictable ids let tests assert exact events and records.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def __init__(self) -> None:
        self.counts = Counter()

    def next_id(self, kind: str) -> str:
        """Return the next id of the kind.

        What: "<kind>-<n>" with n one higher than the last id of that kind.
        When called: each time a service creates something with an identity.
        Why: ids stay unique and predictable.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        self.counts[kind] += 1
        return f"{kind}-{self.counts[kind]}"


class FakeSimulator(Simulator):
    """Simulator that records its calls and returns preset snapshots.

    What: keeps each call in ``calls`` and answers with the preset snapshots in order.
    When called: injected into a service under test that asks for a simulation.
    Why: tests need no real simulation engine and can check what it was asked.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    def __init__(self, snapshots) -> None:
        self.snapshots = list(snapshots)
        self.calls = []

    def simulate(self, scenario, policy, simulation_id):
        """Record the call and return the next preset snapshot.

        What: appends (scenario, policy, simulation_id) to ``calls`` and pops the next snapshot.
        When called: by the service under test.
        Why: lets tests assert the inputs and control the output.
        Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
        """
        self.calls.append((scenario, policy, simulation_id))
        return self.snapshots.pop(0)
