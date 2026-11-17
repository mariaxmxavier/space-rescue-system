"""Reusable transaction-store contract check.

What: ``check_transaction_store_contract`` and its helpers ``initial_state`` and ``raises``.

When: imported by the contract tests of every ``TransactionStore`` adapter.

Why: one shared check lets a future store prove itself without copying the guarantees (FR-005).
"""

from collections.abc import Callable
from dataclasses import replace

from rescue.adapters.ports import TransactionStore
from rescue.application.state import RunState
from rescue.market.models.b3_market import B3Market


def initial_state() -> RunState:
    """Build the empty run state every contract case starts from.

    What: a ``RunState`` with fixed identities and an empty market.

    When: called once per check, before the store is built.

    Why: the same starting state keeps every case independent and its failures readable.
    """
    return RunState(
        application_run_id="RUN-1",
        central_id="CENTRAL-1",
        market=B3Market(market_id="MARKET-RUN-1"),
    )


def raises(error: type[BaseException], action: Callable[[], object]) -> bool:
    """Report whether ``action`` raises ``error``.

    What: runs ``action`` and returns True only if it raised ``error``.

    When: called by the contract check for each case that must raise.

    Why: a bare try/except that passes silently would let a store that swallows errors pass.
    """
    try:
        action()
    except error:
        return True
    return False


def check_transaction_store_contract(make_store: Callable[[RunState], TransactionStore]) -> None:
    """Raise ``AssertionError`` if a store built by ``make_store`` breaks the port contract.

    What: exercises success, a raising operation and a wrong-type result against one store, in that
    order, and checks the published state after each.

    When: called by each test that proves a store conforms or that a broken store is caught.

    Why: these three cases are the transaction-store guarantees TS-1 to TS-3 in contracts/ports.md.
    """
    original = initial_state()
    store = make_store(original)

    assert store.transact(lambda state: (replace(state, command_index=("ok",)), "done")) == "done"
    assert store.snapshot().command_index == ("ok",)
    assert original.command_index == ()

    def fail_after_staging(state: RunState) -> tuple[RunState, None]:
        staged = replace(state, command_index=("lost",))
        raise RuntimeError(f"abort after staging {staged.command_index}")

    assert raises(RuntimeError, lambda: store.transact(fail_after_staging)), (
        "transact must propagate the operation's exception"
    )
    assert store.snapshot().command_index == ("ok",)

    assert raises(TypeError, lambda: store.transact(lambda state: ("not a state", None))), (
        "transact must reject a result that is not a RunState"
    )
    assert store.snapshot().command_index == ("ok",)
