"""Communication identifies what a ship sent, decides how it is delivered and reports the outcome.

What: Holds the message, delivery, session and report models in models and the pure rules in
rules. A ship response becomes an immutable communication message, the delivery rules turn it into
one delivery decision, and only an accepted decision lets the mission rules make a transition; the
use case in rescue/application/central.py gathers the facts and applies the result. The mission
state itself stays in the mission package.
When called: RescueCentral.record_response calls classify_delivery for every ship response, then
accept_inbound and issue_report. The RescueCentral methods synchronise_inbound and recover_reports
call the rules of the same names. receive_report is the ship-side rule that replays reports; the
application does not call it, and the models never call a rule.
Why: Communication is separate from mission accounting because responses can be lost, repeated or
delayed, and identifying what arrived must not decide whether seats change. The B3-style inbound
flow is idempotent: a number below the expected one is never applied again, a gap yields a
NotApplied notification, and later valid messages proceed without waiting. The outbound flow is
recoverable: central keeps each decision report with its original number, so a missing range is
replayed unchanged and never reruns the response or moves seats.
Decisions for one mission follow its B3 matching-engine order, one at a time in first-in,
first-out order, because rescue responses carry no price and so only the arrival time at central
counts. Sender time, session sequence and attempt number never reorder decisions, and a retried
message goes to the back.
Duplicates and identity conflicts are classified by message and delivery identity, a retry keeps
its message identity with a fresh delivery, and loss and delay are visible as gaps rather than
silent failures. A response received exactly at its deadline counts as late, the same as one after it.
Each step has one owner: models hold the facts, rules decide, central applies and publishes.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""
