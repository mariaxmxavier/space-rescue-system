"""Closed vocabulary of delivery dispositions a ship response can receive.

What: the five outcomes a delivery attempt can be decided with, as a StrEnum.
When called: returned with a delivery decision and compared by callers that report it.
Why: one spelling per disposition keeps the rules, the reports and the diagrams from drifting apart.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from enum import StrEnum


class DeliveryDisposition(StrEnum):
    """Final disposition of one delivery attempt: applied, ignored, lost, rejected or late.

    What: the five dispositions, each equal to its wire string.
    When called: returned with a delivery decision; callers compare against these members
      instead of string literals.
    Why: a disposition outside this set fails at construction, so every delivery decision
      uses one closed spelling.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """

    APPLIED = "applied"
    IGNORED = "ignored"
    LOST = "lost"
    REJECTED = "rejected"
    LATE = "late"
