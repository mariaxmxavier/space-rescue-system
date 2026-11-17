"""Record a command and its value in the run's command index.

What: returns the state with one (run, command, operation, payload, value) entry appended.
When called: by open_request once a command has been applied.
Why: the index lets a repeated command id replay its first value instead of acting twice.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.state import RunState


def append_command(state: RunState, command_id: str, operation: str, payload, value):
    """Append command.

    What: returns the state with one (run id, command id, operation, payload, value) entry added to the command index.
    When called: by open_request once a create_request command has been applied.
    Why: the index lets a repeated command id replay its first value instead of acting twice.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    return replace(
        state,
        command_index=(
            *state.command_index,
            (state.application_run_id, command_id, operation, payload, value),
        ),
    )
