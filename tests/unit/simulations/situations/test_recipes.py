"""Check reusable recipe modules remain import-safe and describe actual wire semantics."""

from decimal import Decimal
from importlib import import_module
from pathlib import Path


def test_every_situation_module_can_be_imported_without_io():
    """Catch stale strict-model constructors before profiles attempt to reuse recipes."""
    root = Path(__file__).resolve().parents[4]
    for path in (root / "simulations/services/situations").rglob("*.py"):
        import_module(".".join(path.relative_to(root).with_suffix("").parts))


def test_delayed_and_duplicate_recipes_keep_distinct_message_and_sequence_meanings():
    """A late original send differs from replaying an already accepted message identity."""
    from simulations.models.request_selector import RequestSelector
    from simulations.services.situations.communication.delivery.delayed_response import (
        delayed_response_recipe,
    )
    from simulations.services.situations.communication.delivery.duplicate_response import (
        duplicate_response_recipe,
    )
    from simulations.services.situations.communication.ordering.out_of_order import (
        out_of_order_recipe,
    )

    target = RequestSelector(ship_key="C", occurrence=2)
    late = delayed_response_recipe(target, seats=2, sent_at=Decimal("12"), sequence=3)
    replay = duplicate_response_recipe(target, accepted_seats=2, original_sequence=5)
    obsolete = out_of_order_recipe(target, seats=2, sent_at=Decimal("12"), sequence=2)
    assert late.action.sent_at == Decimal("12")
    assert late.action.sequence > obsolete.action.sequence
    assert replay.action.replay_of
    assert replay.evidence.check_name == "message_replay"
