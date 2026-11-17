"""Exercise case preparation and synchronized timeline playback in the browser.

What: checks real viewer controls against a deterministic HTTP transcript fixture.
When called: pytest runs the simulation browser journeys.
Why: arbitrary seeking must never reveal a different snapshot in another panel.
"""

from __future__ import annotations

from copy import deepcopy

import pytest
from playwright.sync_api import Page, expect

CASES = [
    {
        "id": "baseline",
        "name": "Baseline rescue",
        "description": "Three ships confirm ten seats.",
        "situations": ["full_confirmation"],
        "situation_count": 1,
    },
    {
        "id": "all12",
        "name": "All twelve situations",
        "description": "Rescue with recovery probes.",
        "situations": ["full_confirmation", "cancellation"],
        "situation_count": 12,
    },
]


def transcript(case_id="baseline"):
    """Return snapshots with distinct accounting and two equal-time events."""
    initial = {
        "application_run_id": f"run-{case_id}",
        "missions": [
            {
                "mission_id": "mission",
                "station_name": "Aurora",
                "people_count": 10,
                "requests": [],
                "history": [],
            }
        ],
        "market": {
            "ships": [{"ship_id": "ship-A", "name": "Aster"}],
            "availabilities": [
                {"ship_id": "ship-A", "total_seats": 10, "available": True, "recorded_at": "0"}
            ],
            "offers": [],
            "quotes": [],
            "rfqs": [],
        },
        "decision_index": [],
        "delivery_index": [],
        "message_index": [],
        "session_index": [],
        "policies": [],
        "scenarios": [],
        "completed_runs": [],
    }
    frames = []
    for ordinal, (time, confirmed, pending, label) in enumerate(
        [
            (0, 0, 10, "Requests submitted"),
            (2, 4, 6, "A confirms four"),
            (2, 6, 0, "Partial response closes request"),
            (5, 10, 0, "Rescue complete"),
        ]
    ):
        state = deepcopy(initial)
        state["missions"][0]["requests"] = [
            {
                "request_id": f"request-{ordinal}",
                "ship_id": "ship-A",
                "requested_seats": 10,
                "confirmed_seats": confirmed,
                "outcome": "accepted" if confirmed == 10 else "pending",
            }
        ]
        progress = {
            "demand": 10,
            "confirmed": confirmed,
            "pending": pending,
            "unconfirmed": 10 - confirmed,
            "additional_needed": 10 - confirmed - pending,
            "status": "complete" if confirmed == 10 else "active",
        }
        frames.append(
            {
                "ordinal": ordinal,
                "logical_time": str(time),
                "event_id": f"event-{ordinal}",
                "label": label,
                "action": {"kind": "test"},
                "outcomes": [{"status": "applied", "reason": None}],
                "state": state,
                "progress": progress,
                "evidence": [],
            }
        )
    return {
        "case_id": case_id,
        "run_id": f"run-{case_id}",
        "mission_id": "mission",
        "initial": {
            "logical_time": "0",
            "state": initial,
            "progress": {
                "demand": 10,
                "confirmed": 0,
                "pending": 0,
                "unconfirmed": 10,
                "additional_needed": 10,
                "status": "active",
            },
        },
        "frames": frames,
        "result": {
            "passed": True,
            "matched_situations": ["full_confirmation"],
            "missing_situations": [],
            "failure_detail": None,
        },
    }


@pytest.fixture
def viewer_page(page: Page, web_origin: str):
    """Mount the exported viewer with HTTP calls isolated from manual workspace."""
    page.route("**/simulations/cases", lambda route: route.fulfill(json={"cases": CASES}))
    page.route(
        "**/simulations/cases/*/runs",
        lambda route: route.fulfill(json=transcript(route.request.url.split("/")[-2])),
    )
    page.route(
        f"{web_origin}/viewer-test",
        lambda route: route.fulfill(
            content_type="text/html",
            body="""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/shell/styles.css"><link rel="stylesheet" href="/simulations/styles.css"></head><body><main id="viewer"></main><script type="module">import {registerSimulationViewer} from '/simulations/index.js';const request=async(path,options)=>{const response=await fetch(path,options);const body=await response.json();if(!response.ok)throw new Error(body.detail);return body};registerSimulationViewer({root:document.querySelector('#viewer'),api:{listSimulationCases:()=>request('/simulations/cases'),runSimulationCase:(id)=>request('/simulations/cases/'+id+'/runs',{method:'POST'})}});</script></body></html>""",
        ),
    )
    page.goto(f"{web_origin}/viewer-test")
    return page


def test_starts_paused_and_seeking_updates_all_panels(viewer_page: Page):
    """Show initial state paused, then historical state at any selected instant."""
    page = viewer_page
    expect(page.get_by_role("button", name="Play simulation", exact=True)).to_be_enabled()
    expect(page.locator('[data-metric="confirmed"]')).to_have_text("0")
    expect(page.get_by_text("Paused", exact=True)).to_be_visible()
    page.get_by_label("Logical time", exact=True).fill("3")
    page.get_by_label("Logical time", exact=True).press("Enter")
    expect(page.locator('[data-metric="confirmed"]')).to_have_text("6")
    expect(page.locator('[data-metric="pending"]')).to_have_text("0")
    expect(page.get_by_text("request-2", exact=True)).to_be_visible()
    expect(page.get_by_text("Showing state committed at t=2", exact=False)).to_be_visible()
    page.get_by_label("Logical time", exact=True).fill("1")
    page.get_by_label("Logical time", exact=True).press("Enter")
    expect(page.locator('[data-metric="confirmed"]')).to_have_text("0")
    expect(page.locator('[data-metric="pending"]')).to_have_text("10")
    expect(page.get_by_text("request-0", exact=True)).to_be_visible()


def test_same_time_events_and_replay_remain_individually_reachable(viewer_page: Page):
    """Step through both events at time two, then restore the initial snapshot."""
    page = viewer_page
    page.get_by_role("button", name="Next event", exact=True).click()
    page.get_by_role("button", name="Next event", exact=True).click()
    expect(page.locator('[data-metric="confirmed"]')).to_have_text("4")
    page.get_by_role("button", name="Next event", exact=True).click()
    expect(page.locator('[data-metric="confirmed"]')).to_have_text("6")
    page.get_by_role("button", name="Previous event", exact=True).click()
    expect(page.locator('[data-metric="confirmed"]')).to_have_text("4")
    page.get_by_role("button", name="Reset to beginning", exact=True).click()
    expect(page.locator('[data-metric="pending"]')).to_have_text("0")
    expect(page.get_by_role("button", name="Play simulation", exact=True)).to_be_visible()


def test_play_pause_and_case_switch_reset(viewer_page: Page):
    """Playback advances; a different case is always prepared paused at its beginning."""
    page = viewer_page
    page.get_by_role("button", name="Play simulation", exact=True).click()
    expect(page.get_by_role("button", name="Pause simulation", exact=True)).to_be_visible()
    expect(page.locator('[data-metric="pending"]')).to_have_text("10", timeout=4000)
    page.get_by_role("button", name="Pause simulation", exact=True).click()
    page.get_by_label("Rescue case", exact=True).select_option("all12")
    expect(page.get_by_text("run-all12", exact=True)).to_be_visible()
    expect(page.locator('[data-metric="pending"]')).to_have_text("0")
    expect(page.get_by_role("button", name="Play simulation", exact=True)).to_be_visible()


def test_keyboard_timeline_and_mobile_layout(viewer_page: Page):
    """Native range seeking is keyboard operable without horizontal page overflow."""
    page = viewer_page
    page.set_viewport_size({"width": 360, "height": 800})
    slider = page.get_by_label("Simulation timeline", exact=True)
    slider.focus()
    slider.press("End")
    expect(page.locator('[data-metric="confirmed"]')).to_have_text("10")
    expect(page.get_by_text("Case passed", exact=True)).to_be_visible()
    slider.press("Home")
    expect(page.locator('[data-metric="confirmed"]')).to_have_text("0")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def test_case_error_offers_retry_without_fabricated_state(viewer_page: Page):
    """A failed preparation clears old panels and can be retried explicitly."""
    page = viewer_page
    page.route(
        "**/simulations/cases/all12/runs",
        lambda route: route.fulfill(status=503, json={"detail": "Simulation unavailable"}),
    )
    page.get_by_label("Rescue case", exact=True).select_option("all12")
    expect(page.get_by_role("alert")).to_contain_text("Simulation unavailable")
    expect(page.get_by_role("button", name="Retry case", exact=True)).to_be_visible()
    expect(page.locator('[data-metric="confirmed"]')).to_have_count(0)
    page.unroute("**/simulations/cases/all12/runs")
    page.get_by_role("button", name="Retry case", exact=True).click()
    expect(page.get_by_text("run-all12", exact=True)).to_be_visible()


def test_late_case_response_cannot_replace_new_selection(viewer_page: Page):
    """A previous request cannot populate a newly selected case after arriving late."""
    page = viewer_page
    held = []
    page.route("**/simulations/cases/all12/runs", lambda route: held.append(route))
    page.get_by_label("Rescue case", exact=True).select_option("all12")
    expect(
        page.get_by_text("Preparing All twelve situations through the rescue API…", exact=True)
    ).to_be_visible()
    page.get_by_label("Rescue case", exact=True).select_option("baseline")
    expect(page.get_by_text("run-baseline", exact=True)).to_be_visible()
    assert held
    with page.expect_response("**/simulations/cases/all12/runs"):
        held[0].fulfill(json=transcript("all12"))
    expect(page.get_by_label("Rescue case", exact=True)).to_have_value("baseline")
    expect(page.get_by_text("run-baseline", exact=True)).to_be_visible()


def test_failed_case_result_is_visible_before_playback(viewer_page: Page):
    """An operationally failed case remains inspectable without implying success."""
    page = viewer_page
    recording = transcript("all12")
    recording["result"].update(passed=False, failure_detail="Missing cancellation evidence")
    page.route("**/simulations/cases/all12/runs", lambda route: route.fulfill(json=recording))
    page.get_by_label("Rescue case", exact=True).select_option("all12")
    expect(page.get_by_role("alert")).to_contain_text("Missing cancellation evidence")
    expect(page.get_by_role("button", name="Play simulation", exact=True)).to_be_visible()
    expect(page.get_by_text("Case passed", exact=True)).to_have_count(0)


def test_real_case_viewer_seeks_and_switches_with_authoritative_api(real_viewer_page: Page):
    """Exercise real prepared cases, both directions of seeking and responsive layouts."""
    page = real_viewer_page
    expect(page.get_by_role("button", name="Play simulation", exact=True)).to_be_enabled(
        timeout=30000
    )
    expect(page.locator('[data-metric="confirmed"]')).to_have_text("0")
    expect(page.get_by_text("Paused", exact=True)).to_be_visible()
    page.set_viewport_size({"width": 1440, "height": 1100})
    page.screenshot(path="/tmp/space-rescue-viewer-desktop.png", full_page=True)
    slider = page.get_by_label("Simulation timeline", exact=True)
    slider.focus()
    slider.press("End")
    expect(page.locator('[data-metric="confirmed"]')).to_have_text("10")
    expect(page.get_by_text("Case passed", exact=True)).to_be_visible()
    page.get_by_role("button", name="Reset to beginning", exact=True).click()
    expect(page.locator('[data-metric="confirmed"]')).to_have_text("0")
    page.get_by_label("Rescue case", exact=True).select_option("all12")
    expect(page.get_by_role("button", name="Play simulation", exact=True)).to_be_enabled(
        timeout=30000
    )
    expect(page.locator('[data-metric="confirmed"]')).to_have_text("0")
    slider.focus()
    slider.press("End")
    expect(page.locator('[data-metric="confirmed"]')).to_have_text("10")
    expect(page.get_by_text("Case passed", exact=True)).to_be_visible()
    expect(page.get_by_text("12 / 12 situations observed", exact=True)).to_be_visible()
    page.get_by_label("Logical time", exact=True).fill("24")
    page.get_by_label("Logical time", exact=True).press("Enter")
    expect(page.locator('[data-view="event-outcomes"]')).to_contain_text(
        "Record response · Rejected · invalid_input"
    )
    expect(page.locator('[data-metric="confirmed"]')).to_have_text("6")
    expect(page.locator('[data-metric="pending"]')).to_have_text("4")
    slider.focus()
    slider.press("End")
    page.set_viewport_size({"width": 360, "height": 800})
    page.screenshot(path="/tmp/space-rescue-viewer-mobile.png", full_page=True)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.emulate_media(reduced_motion="reduce")
    page.get_by_role("button", name="Reset to beginning", exact=True).click()
    expect(page.locator('[data-metric="confirmed"]')).to_have_text("0")


def test_nested_api_outcomes_and_tuple_deliveries_are_explained(viewer_page: Page):
    """Render business rejection and delivery classification, beyond an HTTP 200 label."""
    page = viewer_page
    recording = transcript("all12")
    recording["frames"][1]["outcomes"] = [
        {
            "operation": "record_response",
            "input": {"command": {"confirmed_seats": 3}},
            "http_status": 200,
            "result": {"status": "rejected", "reason": "invalid_input", "value": None},
        }
    ]
    recording["frames"][1]["state"]["delivery_index"] = [
        [
            "delivery-late",
            "message-late",
            {"delivery_id": "delivery-late", "disposition": "ignored", "reason": "late"},
        ]
    ]
    page.route("**/simulations/cases/all12/runs", lambda route: route.fulfill(json=recording))
    page.get_by_label("Rescue case", exact=True).select_option("all12")
    page.get_by_role("button", name="Next event", exact=True).click()
    page.get_by_role("button", name="Next event", exact=True).click()
    expect(page.locator('[data-view="event-outcomes"]')).to_contain_text(
        "Record response · Rejected · invalid_input"
    )
    expect(page.get_by_text("Complete delivery-late · Ignored · Late", exact=True)).to_be_visible()


def test_multiple_missions_follow_selected_timeline(viewer_page: Page):
    """Show arriving missions and switch between authoritative progress snapshots."""
    page = viewer_page
    recording = transcript("all12")
    second = {
        "mission_id": "mission-2",
        "station_name": "Vega",
        "people_count": 120,
        "requests": [],
        "history": [],
    }
    recording["frames"][1]["state"]["missions"].append(second)
    recording["frames"][1]["mission_progress"] = {
        "mission": recording["frames"][1]["progress"],
        "mission-2": {
            "demand": 120,
            "confirmed": 30,
            "pending": 20,
            "unconfirmed": 90,
            "additional_needed": 70,
            "status": "needs_more_help",
        },
    }
    page.route("**/simulations/cases/all12/runs", lambda route: route.fulfill(json=recording))
    page.get_by_label("Rescue case", exact=True).select_option("all12")
    page.get_by_role("button", name="Next event", exact=True).click()
    page.get_by_role("button", name="Next event", exact=True).click()
    expect(page.get_by_text("Vega", exact=False).first).to_be_visible()
    page.get_by_label("Inspect mission", exact=True).select_option("mission-2")
    expect(page.locator('[data-metric="demand"]')).to_have_text("120")
    expect(page.locator('[data-metric="confirmed"]')).to_have_text("30")
    page.get_by_role("button", name="Reset to beginning", exact=True).click()
    expect(page.locator('[data-metric="demand"]')).to_have_text("10")
    expect(page.get_by_text("Vega", exact=False)).to_have_count(0)


def test_real_multiple_missions_enter_and_can_be_inspected(real_viewer_page: Page):
    """Inspect authoritative large missions as they enter and after seeking backward."""
    page = real_viewer_page
    page.get_by_label("Rescue case", exact=True).select_option("multi-mission")
    expect(page.get_by_role("button", name="Play simulation", exact=True)).to_be_enabled(
        timeout=30000
    )
    page.get_by_label("Logical time", exact=True).fill("8")
    page.get_by_label("Logical time", exact=True).press("Enter")
    selector = page.get_by_label("Inspect mission", exact=True)
    expect(selector.locator("option")).to_have_count(3)
    selector.select_option(index=1)
    expect(page.locator('[data-metric="demand"]')).to_have_text("120")
    page.get_by_role("button", name="Reset to beginning", exact=True).click()
    expect(page.get_by_label("Inspect mission", exact=True)).to_have_count(0)
    expect(page.locator('[data-metric="demand"]')).to_have_text("10")
    page.get_by_label("Simulation timeline", exact=True).press("End")
    expect(page.get_by_label("Inspect mission", exact=True).locator("option")).to_have_count(4)
    expect(page.get_by_text("12 / 12 situations observed", exact=True)).to_be_visible()


def test_technical_tab_follows_timeline_and_shows_recorded_io(real_viewer_page: Page):
    """Show recorded exchanges by capability without exposing future events."""
    page = real_viewer_page
    expect(page.get_by_role("button", name="Play simulation", exact=True)).to_be_enabled(
        timeout=30000
    )
    page.get_by_role("tab", name="Technical", exact=True).click()
    expect(page.get_by_role("tabpanel", name="Technical")).to_be_visible()
    expect(page.get_by_role("heading", name="Mission center")).to_be_visible()
    expect(page.get_by_role("heading", name="B3 Market")).to_be_visible()
    expect(
        page.get_by_text("internal calls between components are not traced", exact=False)
    ).to_be_visible()
    log = page.locator(".tech-log")
    assert log.locator("li").count() > 0
    initial_count = log.locator("li").count()
    log.locator("details").first.locator("summary").click()
    expect(log.locator("details").first.get_by_role("heading", name="Input")).to_be_visible()
    expect(log.locator("details").first.get_by_role("heading", name="Output")).to_be_visible()
    page.get_by_role("button", name="Next event", exact=True).click()
    assert log.locator("li").count() > initial_count
    page.get_by_role("button", name="Reset to beginning", exact=True).click()
    assert log.locator("li").count() == initial_count
    page.set_viewport_size({"width": 375, "height": 800})
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.get_by_role("tab", name="Technical", exact=True).press("ArrowLeft")
    expect(page.get_by_role("tab", name="Overview", exact=True)).to_be_focused()
