"""Verify CLI profile selection, streaming and failures through real HTTP JSON."""

from fastapi.testclient import TestClient

from rescue.api.app import create_app
from simulations.entrypoints.cli import main


def test_list_and_invalid_selection_never_open_transport():
    """Reject invalid names and list metadata without creating clients or runs."""

    def no_transport(_):
        raise AssertionError("unexpected transport")

    lines = []
    assert main(["list"], writer=lines.append, client_factory=no_transport) == 0
    assert "baseline" in "\n".join(lines)
    assert main(["run", "unknown"], writer=lines.append, client_factory=no_transport) == 2
    assert main([], writer=lines.append, client_factory=no_transport) == 2


def test_cli_runs_all_profiles_and_streams_progress():
    """Run all four cases independently and emit intermediate actions before summaries."""
    lines = []
    assert (
        main(
            ["run", "--all"], writer=lines.append, client_factory=lambda _: TestClient(create_app())
        )
        == 0
    )
    assert sum("PASS" in line for line in lines) == 5
    assert any("t=24" in line and "invalid_input" in line for line in lines)
    assert any("12/12" in line for line in lines)
