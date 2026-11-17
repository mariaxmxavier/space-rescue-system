"""Browser transport contracts for run isolation and recoverable failures.

When: browser operations race with selection or the API becomes unavailable.
Why: authoritative results must never cross selected run generations.
"""

import os

from playwright.sync_api import Page, expect

from tests.e2e.web.support import open_run, operation, submit

API_ORIGIN = os.environ.get("SPACE_RESCUE_TEST_API", "http://127.0.0.1:8000")


def mock_states(page):
    """Provide successful empty state reads while each test controls its own mutations."""
    page.route(f"{API_ORIGIN}/runs/*/state", lambda route: route.fulfill(json={"missions": []}))


def test_can_create_run_and_share_it_between_tabs(workspace_page: Page):
    """Create a browser run and keep its selected identity while changing tabs."""
    page = workspace_page
    mock_states(page)
    page.route(
        f"{API_ORIGIN}/runs",
        lambda route: route.fulfill(
            status=201, json={"application_run_id": "RUN-UI", "central_id": "CENTRAL"}
        ),
    )
    page.get_by_label("Application run ID", exact=True).fill("RUN-UI")
    page.get_by_label("Central ID", exact=True).fill("CENTRAL")
    page.get_by_role("button", name="Create run", exact=True).click()
    expect(page.locator("#selected-run")).to_have_text("RUN-UI")
    page.get_by_role("tab", name="Exploration").click()
    expect(page.locator("#selected-run")).to_have_text("RUN-UI")


def test_open_unknown_run_shows_unavailable_state(workspace_page: Page):
    """A lost in-memory run remains an unavailable result rather than being recreated."""
    page = workspace_page
    page.route(
        f"{API_ORIGIN}/runs/MISSING/state",
        lambda route: route.fulfill(status=404, json={"detail": "unknown run"}),
    )
    open_run(page, "MISSING")
    expect(page.locator("#workspace-error")).to_contain_text("unavailable")


def test_refresh_failure_keeps_snapshot_and_marks_it_stale(workspace_page: Page):
    """Keep the last committed mission visible after a failed subsequent refresh."""
    page = workspace_page
    page.route(
        f"{API_ORIGIN}/runs/STALE/state",
        lambda route: route.fulfill(
            json={"missions": [{"mission_id": "mission", "people_count": 10}]}
        ),
    )
    open_run(page, "STALE")
    expect(page.locator("#mission-summary")).to_contain_text("mission")
    page.route(
        f"{API_ORIGIN}/runs/STALE/state",
        lambda route: route.fulfill(status=503, json={"detail": "offline"}),
    )
    page.get_by_role("button", name="Refresh state", exact=True).click()
    expect(page.locator("#refresh-status")).to_contain_text("stale")
    expect(page.locator("#mission-summary")).to_contain_text("mission")


def test_history_is_loaded_only_after_explicit_action(workspace_page: Page):
    """Do not grow call history through implicit routine history reads."""
    page = workspace_page
    mock_states(page)
    calls = []

    def history(route):
        calls.append(route.request.url)
        route.fulfill(json=[])

    page.route(f"{API_ORIGIN}/runs/HISTORY/history", history)
    open_run(page, "HISTORY")
    expect(page.locator("#refresh-status")).to_contain_text("Updated")
    assert calls == []
    page.get_by_role("button", name="Load call history", exact=True).click()
    expect(page.locator("#history-content pre")).to_have_text("[]")
    assert len(calls) == 1


def test_operation_rejection_preserves_values_and_is_not_retried(workspace_page: Page):
    """A valid submission may be rejected while preserving all fields for correction."""
    page = workspace_page
    mock_states(page)
    calls = []

    def reject(route):
        calls.append(route.request.url)
        route.fulfill(json={"status": "rejected", "reason": "invalid mission", "value": None})

    page.route(f"{API_ORIGIN}/runs/REJECT/operations/register_mission", reject)
    open_run(page, "REJECT")
    form = submit(
        page,
        "register_mission",
        {"mission_id": "m", "station_name": "Aurora", "people_count": 10, "created_at": "0"},
    )
    expect(form.get_by_role("alert")).to_contain_text("invalid mission")
    expect(form.get_by_label("Station name", exact=True)).to_have_value("Aurora")
    assert len(calls) == 1


def test_uncertain_mutation_is_not_retried(workspace_page: Page):
    """An interrupted connection yields an explicit uncertain result and no resubmission."""
    page = workspace_page
    mock_states(page)
    calls = []

    def disconnect(route):
        calls.append(route.request.url)
        route.abort("connectionreset")

    page.route(f"{API_ORIGIN}/runs/UNCERTAIN/operations/register_mission", disconnect)
    open_run(page, "UNCERTAIN")
    form = operation(page, "register_mission")
    for name, value in {
        "mission_id": "m",
        "station_name": "Aurora",
        "people_count": "10",
        "created_at": "0",
    }.items():
        form.locator(f'[name="{name}"]').fill(value)
    form.get_by_role("button", name="Register mission", exact=True).click()
    expect(form.get_by_role("alert")).to_contain_text("uncertain")
    assert len(calls) == 1


def test_stale_operation_error_cannot_cross_run_selection(workspace_page: Page):
    """Ignore both errors and values from an earlier selection, even after reopening its ID."""
    page = workspace_page
    mock_states(page)
    deferred = []
    page.route(
        f"{API_ORIGIN}/runs/A/operations/register_mission", lambda route: deferred.append(route)
    )
    open_run(page, "A")
    form = operation(page, "register_mission")
    for name, value in {
        "mission_id": "m",
        "station_name": "Aurora",
        "people_count": "10",
        "created_at": "0",
    }.items():
        form.locator(f'[name="{name}"]').fill(value)
    form.get_by_role("button", name="Register mission", exact=True).click()
    expect(form.get_by_role("button", name="Submitting…", exact=True)).to_be_disabled()
    open_run(page, "B")
    open_run(page, "A")
    assert len(deferred) == 1
    deferred[0].fulfill(status=400, json={"detail": "old failure"})
    expect(form.get_by_role("button", name="Register mission", exact=True)).to_be_enabled()
    expect(form.locator(".form-result")).to_be_empty()


def test_latest_state_request_wins_over_delayed_reply(workspace_page: Page):
    """A delayed old snapshot cannot overwrite a newer refresh in the same run."""
    page = workspace_page
    deferred = []
    page.route(f"{API_ORIGIN}/runs/LATEST/state", lambda route: deferred.append(route))
    open_run(page, "LATEST")
    page.route(
        f"{API_ORIGIN}/runs/LATEST/state",
        lambda route: route.fulfill(json={"missions": [{"mission_id": "new", "people_count": 10}]}),
    )
    page.get_by_role("button", name="Refresh state", exact=True).click()
    expect(page.locator("#mission-summary")).to_contain_text("new")
    deferred[0].fulfill(json={"missions": [{"mission_id": "old", "people_count": 1}]})
    expect(page.locator("#mission-summary")).not_to_contain_text("old")


def test_api_url_builder_encodes_run_identifier(workspace_page: Page):
    """Encode run IDs containing slashes in transport paths."""
    page = workspace_page
    paths = []

    def capture(route):
        paths.append(route.request.url)
        route.fulfill(json={"missions": []})

    page.route(f"{API_ORIGIN}/runs/**/state", capture)
    open_run(page, "RUN/ONE")
    expect(page.locator("#refresh-status")).to_contain_text("Updated")
    assert paths[0].endswith("/runs/RUN%2FONE/state")


def test_pending_creation_does_not_replace_a_newer_selected_run(workspace_page: Page):
    """A completed create request retains its result without reopening an abandoned selection."""
    page = workspace_page
    mock_states(page)
    deferred = []
    page.route(f"{API_ORIGIN}/runs", lambda route: deferred.append(route))
    page.get_by_label("Application run ID", exact=True).fill("OLD")
    page.get_by_label("Central ID", exact=True).fill("central")
    page.get_by_role("button", name="Create run", exact=True).click()
    open_run(page, "NEW")
    assert len(deferred) == 1
    deferred[0].fulfill(status=201, json={"application_run_id": "OLD", "central_id": "central"})
    expect(page.get_by_role("button", name="Create run", exact=True)).to_be_enabled()
    expect(page.locator("#selected-run")).to_have_text("NEW")
