"""Retained decision reports and the requests and controls that recover them.

What: central's sequenced decision reports, recovery requests, sequence controls and report cursors.
When called: imported by the recovery rules and by the application that replays reports.
Why: retained reports can be replayed in order without issuing new sequence numbers or reapplying seats.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""
