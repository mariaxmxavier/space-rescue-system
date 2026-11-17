# Contract: Mission docstrings

Every module, class and public function in `rescue/mission/` carries a docstring with these four
labelled parts, in this order (FR-002). Private helpers (`_name` or inside an `_module.py`) need
`What:` and `Why:` only.

```python
"""One-line summary.

What: what it is or does, in domain words.
When called: who calls it and at which moment of a rescue run.
Why: the reason it exists or the rule it protects.
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
"""
```

Example: `SeatRequest`

```text
A ship's request to confirm seats for one mission.

What: one ask to one ship for N seats, pending until a final outcome closes it.
When called: built by RescueCentral when it mobilises a ship; replaced by apply_outcome when the
  ship answers, the request is cancelled, or its deadline passes.
Why: pending seats must be tracked per ship so a refusal or expiry releases exactly that ship's
  share and a closed answer can never change (Constitution II).
Diagram: docs/architecture/diagrams/rescue-domain-model/namespaces/MissionOperations/class-diagram.mmd
```

Rules:

- `Diagram:` is a repo-relative path that exists; it names the MissionOperations class diagram for
  classes and rules, and may add the ER diagram on a second line.
- Do not describe history ("moved from models.py"). Say what is true now.
- Inline `#` comments are still not used (global rule); the docstring is the one place for intent.

Verification: `tests/architecture/mission_layout/test_docstrings.py`.
