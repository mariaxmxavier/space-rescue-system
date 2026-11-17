"""Ship sessions with independent inbound and outbound sequence counters.

What: a ship's logical exchange with central, its session envelope and its gap notices.
When called: imported by the session rules and by the application that sequences responses.
Why: each direction keeps its own counter, so a missed message is visible without blocking others.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""
