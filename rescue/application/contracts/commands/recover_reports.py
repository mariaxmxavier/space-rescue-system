"""The RecoverReports command contract.

What: defines the command that replays retained decision reports of a session.
When called: imported by RescueCentral.recover_reports, the recover_reports service and callers that build the command.
Why: a command is one frozen value, so a service receives its input already shaped and unchangeable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import Id


@dataclass(frozen=True, slots=True)
class RecoverReports:
    """Re-read the retained decision reports of one session version, in outbound order.

    What: names the session, its version, the first outbound sequence wanted and how many to return.
    When called: by a ship that has missed decision reports and needs them replayed, through RescueCentral.recover_reports and the recover_reports service.
    Why: a recovered report must match the original (same id and sequence), so recovery replays
      history and never recomputes it.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    session_id: Id
    version: int
    from_sequence: int
    count: int
