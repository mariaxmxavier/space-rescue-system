"""Find the stored entry of a command in this run.

What: returns the (run, command, operation, payload, value) entry with this command id, or None.
When called: by open_request and accept_quote before they act on a command.
Why: a repeated command id must replay its first result or be refused as a conflict.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from rescue.state import RunState


def command_entry(state: RunState, command_id: str):
    """Command entry.

    What: returns the command index entry of this run with this command id, or None.
    When called: by open_request and by accept_quote to detect a repeated command.
    Why: a repeated command id must be recognised before any work, so it can replay or report identity_conflict.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """
    return next(
        (
            item
            for item in state.command_index
            if isinstance(item, tuple)
            and len(item) == 5
            and item[0] == state.application_run_id
            and item[1] == command_id
        ),
        None,
    )
