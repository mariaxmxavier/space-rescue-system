"""Mission: one rescue job's seat accounting.

What: the package holding Mission, its seat requests, and the rules that change them.
When called: imported by callers that register missions, apply outcomes or read progress.
Why: keeps seat accounting (Constitution I and II) in one pure package with no I/O.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""
