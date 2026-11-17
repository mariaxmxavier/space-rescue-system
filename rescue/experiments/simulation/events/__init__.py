"""The scenario event handlers of one simulation run.

What: a package marker for the handlers that apply availability, expiry and response events.
When called: imported module by module by the runner when it plays a timeline event.
Why: one module per event kind keeps each handler small, and nothing is re-exported here.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""
