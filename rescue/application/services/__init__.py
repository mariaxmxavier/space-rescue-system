"""The application services, one folder per capability.

What: holds the use cases RescueCentral delegates to, one function per module.
When called: imported by RescueCentral, which hands each command to its service.
Why: keeps each use case small and testable on its own instead of one large class.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""
