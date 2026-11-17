"""Services that ask for, record, accept, reject and expire quotes.

What: holds the request_quotes, record_quote, accept_quote, reject_quote and expire_quotes services.
When called: imported by RescueCentral.request_quotes, record_quote, accept_quote, reject_quote and expire_quotes.
Why: groups the quote use cases away from the fleet, request and communication services.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""
