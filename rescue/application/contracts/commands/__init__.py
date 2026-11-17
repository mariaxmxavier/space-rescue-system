"""The application command contracts, one module per command.

What: holds one frozen command value per use case.
When called: imported through rescue.application.contracts, which re-exports every command.
Why: one module per command keeps each contract small and easy to find.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""
