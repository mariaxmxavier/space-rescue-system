"""The ship's place in central's ordered decision reports, with reports that arrived early.

What: the session, version and next report sequence a ship expects, plus the reports held back because they arrived ahead of it.
When called: kept by the ship side while it receives reports, and read to decide which report to apply next or which to request again.
Why: reports must be applied in sequence, so early ones are buffered in order and never alongside a gap they would hide.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
  docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
"""

from __future__ import annotations

from dataclasses import dataclass

from rescue.communication.models.recovery.decision_report import DecisionReport
from rescue.values import DomainValidationError, Id, normalize_id, normalize_positive_quantity


@dataclass(frozen=True, slots=True)
class ReportCursor:
    """The ship's next expected report and the early reports it is holding.

    What: names the session and version, the next report sequence expected, and the buffered reports in sequence order.
    When called: created when a ship starts or resumes receiving reports and replaced as reports are applied or buffered.
    Why: a buffered report must lie beyond the expected one, in strict order and in the same session version, so a gap or a replay cannot be stored.
    Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/class-diagram.mmd
      docs/architecture/diagrams/rescue-domain-model/namespaces/Communication/entity-relationship-diagram.mmd
    """

    session_id: Id
    version: int
    next_expected: int
    buffered: tuple[DecisionReport, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "session_id", normalize_id(self.session_id))
        object.__setattr__(self, "version", normalize_positive_quantity(self.version))
        object.__setattr__(self, "next_expected", normalize_positive_quantity(self.next_expected))
        buffered = tuple(self.buffered)
        if not all(isinstance(item, DecisionReport) for item in buffered):
            raise DomainValidationError("buffered must hold decision reports")
        envelopes = [item.envelope for item in buffered]
        if any(e.session_id != self.session_id or e.version != self.version for e in envelopes):
            raise DomainValidationError("buffered reports must share the same session and version")
        sequences = [e.sequence for e in envelopes]
        if any(sequence <= self.next_expected for sequence in sequences):
            raise DomainValidationError("buffered reports must be after next_expected")
        if any(a >= b for a, b in zip(sequences, sequences[1:])):
            raise DomainValidationError("buffered reports must be strictly increasing by sequence")
        object.__setattr__(self, "buffered", buffered)
