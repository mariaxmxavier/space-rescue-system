"""Apply one received decision report to the ship's report cursor.

What: delivers a report that is next in sequence together with any buffered reports that follow it, buffers a later report, and ignores an old or repeated one.
When called: the ship side calls it for every decision report that arrives, before applying the reports it returns.
Why: reports must be applied in order and at most once, and a pure rule shows the gap to request without touching storage.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from dataclasses import replace

from rescue.communication.models.recovery.decision_report import DecisionReport
from rescue.communication.models.recovery.report_cursor import ReportCursor


def receive_report(
    cursor: ReportCursor, report: DecisionReport
) -> tuple[ReportCursor, tuple[DecisionReport, ...], tuple[int, int] | None]:
    """Return the new cursor, the reports now deliverable in order, and any gap to request.

    What: a report at next_expected is delivered and the consecutive buffered reports drain after it;
      a later report is buffered and the gap is the leading run of missing reports, from next_expected
      up to the earliest buffered report (the arriving one included); an earlier or already buffered report returns the cursor unchanged.
    When called: once per arriving report, with the cursor the ship currently holds.
    Why: the gap is a contiguous run of truly missing reports, so a recovery request never repeats a buffered report and never skips a missing one.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """
    sequence = report.envelope.sequence
    expected = cursor.next_expected
    if sequence < expected or any(item.envelope.sequence == sequence for item in cursor.buffered):
        return cursor, (), None
    if sequence > expected:
        buffered = tuple(
            sorted((*cursor.buffered, report), key=lambda item: item.envelope.sequence)
        )
        gap = (expected, buffered[0].envelope.sequence - expected)
        return replace(cursor, buffered=buffered), (), gap
    delivered = [report]
    rest = list(cursor.buffered)
    while rest and rest[0].envelope.sequence == expected + len(delivered):
        delivered.append(rest.pop(0))
    return (
        replace(cursor, next_expected=expected + len(delivered), buffered=tuple(rest)),
        tuple(delivered),
        None,
    )
