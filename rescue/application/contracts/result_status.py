"""The outcome category of one application command.

What: the four statuses a command can end in: applied, replayed, rejected or ignored.
When called: by every service when it builds a Result, and by callers that branch on the outcome.
Why: one closed set keeps the outcome of a command checkable instead of a free string.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
"""

from enum import StrEnum


class ResultStatus(StrEnum):
    """The closed set of outcomes of a command.

    What: names the outcomes applied, replayed, rejected and ignored.
    When called: read by services when they build a Result, and by callers that branch on the outcome.
    Why: a Result refuses any status outside this set, so the outcome is never a free string.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Application/class-diagram.mmd
    """

    APPLIED = "applied"
    REPLAYED = "replayed"
    REJECTED = "rejected"
    IGNORED = "ignored"
