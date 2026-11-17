"""Seeded broken ``IdSource`` double that returns the same ID for every call of a kind.

What: one class, ``RepeatsIds``, used as the broken source in the ID-source contract.

When: imported only by ``test_id_source_contract.py``.

Why: a contract check that cannot fail proves nothing; this double shows the check catches a source
that repeats IDs.
"""

from rescue.adapters.ports import IdSource


class RepeatsIds(IdSource):
    """A deliberately broken source that always returns the same ID for a kind.

    What: returns ``<kind>-1`` on every call.

    When: used only by the test proving that the contract check fails on a repeating source.

    Why: the seeded fault the ID-source contract must catch.
    """

    def next_id(self, kind: str) -> str:
        """Return the same ID for every call of a kind.

        What: ``<kind>-1``.

        When: called by the contract check in place of a real source.

        Why: the seeded fault the contract must catch.
        """
        return f"{kind}-1"
