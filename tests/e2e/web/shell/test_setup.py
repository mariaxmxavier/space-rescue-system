"""Verify root run setup feedback and duplicate submission protection."""

from playwright.sync_api import Page, expect


def test_opening_without_a_run_id_has_actionable_feedback(workspace_page: Page):
    """Reject an empty identifier locally and return focus to the field for correction."""
    page = workspace_page
    page.get_by_role("button", name="Open run", exact=True).click()
    expect(page.locator("#workspace-error")).to_contain_text("Enter a run ID")
    expect(page.get_by_label("Application run ID", exact=True)).to_be_focused()


def test_run_creation_disables_duplicate_submissions_and_preserves_input(workspace_page: Page):
    """Submit one command while pending and restore controls after a transport rejection."""
    page = workspace_page
    requests = []
    page.route("**/runs", lambda route: requests.append(route))
    page.get_by_label("Application run ID", exact=True).fill("pending-run")
    page.get_by_label("Central ID", exact=True).fill("central")
    page.get_by_role("button", name="Create run", exact=True).click()
    expect(page.get_by_role("button", name="Creating run…", exact=True)).to_be_disabled()
    page.locator("#run-form").evaluate(
        "form => form.dispatchEvent(new Event('submit', {bubbles:true, cancelable:true}))"
    )
    assert len(requests) == 1
    requests[0].fulfill(status=409, json={"detail": "run already exists"})
    expect(page.locator("#workspace-error")).to_contain_text("run already exists")
    expect(page.get_by_role("button", name="Create run", exact=True)).to_be_enabled()
    expect(page.get_by_label("Application run ID", exact=True)).to_have_value("pending-run")


def test_tabs_restore_the_selected_capability_and_active_navigation(workspace_page: Page):
    """Keep the prior capability visible when switching back to its workspace mode."""
    page = workspace_page
    page.get_by_role("button", name="Communication", exact=True).click()
    expect(page.locator('form[data-operation="record_response"]')).to_be_visible()
    page.get_by_role("tab", name="Operations", exact=True).click()
    expect(page.locator('form[data-operation="register_mission"]')).to_be_visible()
    expect(page.get_by_role("button", name="Missions", exact=True)).to_have_attribute(
        "aria-current", "true"
    )
    page.get_by_role("tab", name="Exploration", exact=True).click()
    expect(page.locator('form[data-operation="record_response"]')).to_be_visible()
    expect(page.get_by_role("button", name="Communication", exact=True)).to_have_attribute(
        "aria-current", "true"
    )
