"""The delivery steps that record_response runs in order.

What: normalise, classify, resolve the session and publish one ship response delivery.
When called: imported by record_response, one function per module.
Why: the response body is split into steps that each fit on a screen and keep the same behaviour.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""
