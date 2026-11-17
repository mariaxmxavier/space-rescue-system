"""The run state value shared by the application and its adapters.

What: exports RunState from rescue.state.run_state.
When called: whenever application code or an adapter needs the run state type.
Why: a neutral package lets adapters depend on the state without importing the application layer.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/entity-relationship-diagram.mmd
"""

from rescue.state.run_state import RunState

__all__ = ["RunState"]
