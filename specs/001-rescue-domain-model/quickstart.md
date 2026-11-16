# Quickstart and acceptance scenarios

Use CPython 3.14.10 as pinned in `.python-version`. The project has no third-party runtime dependencies. Run commands from the repository root.

## Try the callable API

```python
from rescue.application.contracts import RegisterMission
from rescue.bootstrap import new_run

context = new_run("RUN-1", "CENTRAL-1")
central = context.central
central.register_mission(
    RegisterMission(
        mission_id="MISSION-1",
        station_name="North Station",
        people_count=10,
        created_at=0,
    )
)
progress = central.get_progress("MISSION-1", now=0).value
print(progress.confirmed, progress.pending, progress.additional_needed)
```

The initial result is `0 0 10`. Operations return immutable `Result` values; inspect `status`, `value`, and `reason`. The callable API and remaining command fields are in [contracts](contracts/callable-api.md).

## Exercise the scenarios

Each scenario below is covered by the listed standard-library `unittest` suites. Run one suite with `python -m unittest discover -s tests -p "test_NAME.py" -v`, replacing `NAME` with a listed file name.

1. **Mission accounting:** request 6 for demand 10, partially accept 4, and verify confirmed=4, pending=0, and additional_needed=6. Pending seats do not complete a mission. See `test_mission.py`.
2. **Shared ship capacity:** hold 4 seats against capacity 6, then race two further 4-seat holds; at most one may apply. Accepting a quote transfers the hold into pending exactly once. See `test_market.py`, `test_central.py`, and `test_concurrency.py`.
3. **Changing availability and offers:** a capacity reduction keeps existing requests and exposes any shortfall; new requests cannot exceed current inventory. Highest revision number remains current even when timestamps are reversed. See `test_market.py` and `test_central.py`.
4. **Retries and message identity:** identical command retries return the original request; changed command content conflicts. Duplicate, unknown, late, and closed-request responses add delivery diagnostics without adding extra applied history. See `test_central.py` and `test_communication.py`.
5. **Timing and expiry:** submit at 10 and receive at 17 for a 7-second response elapsed time. Receipt at deadline 20 expires first. Delays of 2 outbound + 5 decision + 3 return report 10 seconds elapsed and 5 seconds communication RTT. See `test_timing.py` and `test_communication.py`.
6. **Scenario comparison and resilience:** compare both policies from the same baseline; run ordinary, partial/refusal, and delayed/lost/capacity-change fixtures. Same-seed runs match, lost responses retain no receipt, and operational state stays unchanged. See `test_experiments.py`, `test_comparison.py`, and `test_resilience.py`.
7. **Run boundaries and architecture:** a new context has independent mission and history state; bool, fractional, blank, negative, and non-finite inputs are rejected. Domain modules remain inward-facing. See `test_values.py`, `test_central.py`, `test_architecture.py`, and `test_memory.py`.

## Run all checks and the demonstration

```powershell
python --version
python -m unittest discover -s tests -p "test_*.py" -v
python -m rescue.demo
```

The demo coordinates demand 10 across multiple ships, including partial acceptance, refusal, and another mobilisation. Completion is reported only after all 10 seats are confirmed. It also compares two policies across the three scenario types in item 6. The executed results are recorded in [validation.md](validation.md).
