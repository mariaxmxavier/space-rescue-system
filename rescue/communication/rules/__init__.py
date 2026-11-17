"""Pure communication rules that classify deliveries, sequence sessions and recover reports.

What: the public rules the application calls to decide communication outcomes.
When called: invoked by the application for each response, session command or recovery request.
Why: rules are free of storage, clocks and I/O, so each decision is verified in isolation.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from rescue.communication.rules.accept_inbound import accept_inbound
from rescue.communication.rules.classify_delivery import classify_delivery
from rescue.communication.rules.issue_report import issue_report
from rescue.communication.rules.receive_report import receive_report
from rescue.communication.rules.recover_reports import recover_reports
from rescue.communication.rules.synchronise_inbound import synchronise_inbound

__all__ = [
    "classify_delivery",
    "accept_inbound",
    "issue_report",
    "recover_reports",
    "synchronise_inbound",
    "receive_report",
]
