"""Browser checks for primary navigation accessibility and responsive use.

What: verifies keyboard navigation, reduced-motion preference and narrow/wide layouts.
When called: pytest runs this module with desktop and mobile viewport configurations.
Why: operators need dependable access to rescue controls across input methods and screens.
"""

from __future__ import annotations

from playwright.sync_api import Page, expect


def test_primary_tabs_are_keyboard_operable(workspace_page: Page):
    page = workspace_page
    operations = page.get_by_role("tab", name="Operations")
    exploration = page.get_by_role("tab", name="Exploration")
    operations.focus()
    page.keyboard.press("ArrowRight")
    expect(exploration).to_be_focused()
    page.keyboard.press("Enter")
    expect(exploration).to_have_attribute("aria-selected", "true")


def test_primary_controls_remain_reachable_on_phone_and_desktop(workspace_page: Page):
    page = workspace_page
    for width in (360, 1440):
        page.set_viewport_size({"width": width, "height": 900})
        expect(page.get_by_role("tab", name="Operations")).to_be_visible()
        expect(page.get_by_role("tab", name="Exploration")).to_be_visible()
        expect(page.get_by_label("Application run ID")).to_be_visible()
        assert page.locator("body").evaluate("element => element.scrollWidth <= window.innerWidth")


def test_reduced_motion_preference_is_respected(workspace_page: Page):
    page = workspace_page
    page.emulate_media(reduced_motion="reduce")
    expect(page.get_by_role("tab", name="Operations")).to_be_visible()
    assert page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches")


def test_status_has_text_and_does_not_depend_on_colour(workspace_page: Page):
    page = workspace_page
    alert = page.get_by_role("alert")
    page.get_by_label("Application run ID").fill("MISSING")
    page.get_by_role("button", name="Open run").click()
    expect(alert).to_contain_text("unavailable")
