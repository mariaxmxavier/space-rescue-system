"""Collect the identities a run baseline already uses.

What: `baseline_identity_ids` returns the sorted ids found in `_id` fields and the index keys.
When called: by the runner before it starts a run, to reserve those ids.
Why: a fresh run must not mint an id that the baseline already holds.
Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass

from rescue.experiments.models import RunBaseline


def baseline_identity_ids(baseline: RunBaseline) -> tuple[str, ...]:
    """Collect typed identities and raw keys carried by baseline indexes.

    What: walks the baseline's tuples and dataclasses for `*_id` strings, then adds the ids in the
      command and delivery index entries, and returns them sorted.
    When called: once per run, before the central is started.
    Why: the reserved ids keep the new run from reusing an identity the baseline holds.
    Diagram: docs/architecture/diagrams/rescue-domain-model/class-diagrams/scenario-model.mmd
    """
    identities: set[str] = set()

    def collect(value: object) -> None:
        if isinstance(value, tuple):
            for item in value:
                collect(item)
        elif is_dataclass(value):
            for field in fields(value):
                item = getattr(value, field.name)
                if field.name.endswith("_id") and isinstance(item, str):
                    identities.add(item)
                collect(item)

    collect(baseline)
    for entry in baseline.command_index:
        if isinstance(entry, tuple) and len(entry) == 5 and isinstance(entry[1], str):
            identities.add(entry[1])
    for entry in baseline.delivery_index:
        if isinstance(entry, tuple) and len(entry) == 3:
            identities.update(value for value in entry[:2] if isinstance(value, str))
    return tuple(sorted(identities))
