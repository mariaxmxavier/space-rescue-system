"""Logical communication messages, independent of how many times they are delivered.

What: the immutable message content a ship sends in response to a request.
When called: imported by the models and rules that correlate deliveries with messages.
Why: message identity and content stay fixed across retries, so duplicates can be recognised.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""
