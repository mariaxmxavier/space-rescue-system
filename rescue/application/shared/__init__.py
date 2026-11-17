"""Small helpers shared by the application services.

What: lookups, replacements and result builders that read or rewrite a RunState.
When called: imported by the service modules, one function per module.
Why: services share one definition of each lookup instead of each carrying a private copy.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""
