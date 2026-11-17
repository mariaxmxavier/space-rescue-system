"""Reusable ID-source contract check.

What: ``check_id_source_contract``.

When: imported by the contract tests of every ``IdSource`` adapter.

Why: one shared check lets a future source prove itself without copying the guarantee (FR-005).
"""

from collections.abc import Callable

from rescue.adapters.ports import IdSource


def check_id_source_contract(make_source: Callable[[], IdSource]) -> None:
    """Raise ``AssertionError`` if IDs drawn from one source ever repeat.

    What: draws 150 IDs across two kinds from one new source and asserts that none repeats.

    When: called by the tests that prove the sequence source conforms and that a repeating source
    is caught.

    Why: uniqueness within one run is the ID-source guarantee in contracts/ports.md (ID-1).
    """
    source = make_source()
    drawn = [source.next_id(kind) for kind in ("request", "message", "request") * 50]
    assert len(drawn) == len(set(drawn))
