"""The SynchroniseInbound command contract.

What: defines the control that moves the expected inbound number of a session.
When called: imported by RescueCentral.synchronise_inbound, the synchronise_inbound service and callers that build the command.
Why: a command is one frozen value, so a service receives its input already shaped and unchangeable.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.values import Id


@dataclass(frozen=True, slots=True)
class SynchroniseInbound:
    """Tell central which inbound sequence number the ship sends next.

    What: names the session, its version and the next inbound sequence number.
    When called: by a ship that skips inbound numbers, so central records them as not applied, through RescueCentral.synchronise_inbound and the synchronise_inbound service.
    Why: a gap otherwise stays open until a message fills it, and this control advances the
      expected number without consuming a business number.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    session_id: Id
    version: int
    next_sequence: int
