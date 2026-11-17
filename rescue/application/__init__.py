"""Application use cases; the ports they depend on live in ``rescue.adapters.ports``.

What: the package of the application layer: the RescueCentral facade, the contracts, the services and the shared helpers.
When called: imported by bootstrap, the demo, the experiments and the tests, always through its submodules.
Why: the layer depends only on ports, never on adapters, so it stays testable (import contract application-no-memory).
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""
