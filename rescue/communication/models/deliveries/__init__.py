"""Individual delivery attempts and the facts and decisions that classify them.

What: the attempt to receive a message, its gathered facts and the decision that classifies it.
When called: imported by the classification rule and by the application that records deliveries.
Why: separating facts from decisions lets the delivery rule be tested without storage or a clock.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""
