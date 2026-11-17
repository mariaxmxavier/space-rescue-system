"""Guards the comparison entrypoint `python -m benchmarks.mobilisation.compare`.

Covers the five-family default (largest_capacity excluded), the table header and
one row per algorithm per scenario, table-only normal output, and the `--trace`
JSON-lines shape. Trace lines go to stdout, before each table. Timing is never asserted.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
FAMILIES = {"earliest_arrival", "priority_queue", "min_cost_flow", "cp_sat", "knapsack"}
COLUMNS = [
    "scenario",
    "algorithm",
    "seats_covered",
    "last_seat_arrival_s",
    "ships_used",
    "unused_seats",
    "runtime_ms",
]
SCENARIO_COUNT = 5


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "benchmarks.mobilisation.compare", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


def cells(line: str) -> list[str]:
    return [c for c in re.split(r"\s*\|\s*|\s{2,}|,|\t", line.strip(" |")) if c]


def table_rows(stdout: str) -> list[list[str]]:
    rows = [cells(line) for line in stdout.splitlines() if not line.startswith("{")]
    return [r for r in rows if len(r) >= len(COLUMNS)]


def data_rows(stdout: str) -> list[list[str]]:
    return [r for r in table_rows(stdout) if r[1] in FAMILIES | {"largest_capacity"}]


@pytest.fixture(scope="module")
def default_run() -> subprocess.CompletedProcess[str]:
    return run()


@pytest.fixture(scope="module")
def trace_run() -> subprocess.CompletedProcess[str]:
    return run("--trace")


def trace_lines(stdout: str) -> list[dict]:
    return [json.loads(line) for line in stdout.splitlines() if line.startswith("{")]


def test_default_run_exits_zero(default_run):
    assert default_run.returncode == 0, default_run.stderr


def test_default_run_covers_exactly_five_families(default_run):
    assert {r[1] for r in data_rows(default_run.stdout)} == FAMILIES


def test_largest_capacity_is_not_a_default_row(default_run):
    assert "largest_capacity" not in default_run.stdout


def test_table_header_has_all_columns(default_run):
    assert any(r[: len(COLUMNS)] == COLUMNS for r in table_rows(default_run.stdout))


def test_one_row_per_algorithm_per_scenario(default_run):
    rows = data_rows(default_run.stdout)
    pairs = {(r[0], r[1]) for r in rows}
    assert len(rows) == len(pairs) == len(FAMILIES) * SCENARIO_COUNT
    assert len({r[0] for r in rows}) == SCENARIO_COUNT


def test_normal_output_has_no_trace_lines(default_run):
    assert not [ln for ln in default_run.stdout.splitlines() if ln.startswith("{")]


def test_trace_run_exits_zero(trace_run):
    assert trace_run.returncode == 0, trace_run.stderr


def test_trace_lines_have_required_fields(trace_run):
    lines = trace_lines(trace_run.stdout)
    assert lines
    assert all({"algorithm", "step", "ship_id", "detail"} <= set(d) for d in lines)


def test_trace_algorithms_are_the_five_families(trace_run):
    assert {d["algorithm"] for d in trace_lines(trace_run.stdout)} == FAMILIES


def test_trace_has_final_result_step_per_run(trace_run):
    lines = trace_lines(trace_run.stdout)
    results = [d for d in lines if d["step"] == "result"]
    assert {d["algorithm"] for d in results} == FAMILIES
    assert len(results) >= len(FAMILIES) * SCENARIO_COUNT
