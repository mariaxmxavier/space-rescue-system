"""Check nested browser editors against the actual run-creation codec.

When: browser verification exercises configurable experiment baselines.
Why: every supported nested field must be editable without authoring JSON.
"""

from fastapi.testclient import TestClient
from playwright.sync_api import Page, expect

from rescue.api.app import create_app


def test_nested_scenario_editor_round_trips_real_api(page: Page, web_origin: str):
    """Compose multiple entities and response rules using repeatable browser controls."""
    page.goto(web_origin)
    page.evaluate("""async () => {
      const { createValueEditor } = await import('/shared/ui/value-editor.js');
      const { scenarioSchema } = await import('/experiments/configuration/schemas.js');
      document.body.replaceChildren();
      const editor = createValueEditor(scenarioSchema, 'Scenario');
      document.body.append(editor.element);
      window.testEditor = editor;
    }""")
    page.get_by_label("Scenario ID", exact=True).fill("scenario")
    page.get_by_label("Revision", exact=True).fill("1")
    page.get_by_label("Name", exact=True).fill("Rescue")
    page.get_by_label("Time horizon seconds", exact=True).fill("10.5")
    page.get_by_label("Seed", exact=True).fill("1")
    page.get_by_label("Event budget", exact=True).fill("100")
    page.get_by_label("Market ID", exact=True).fill("market")
    page.get_by_role("button", name="Add mission", exact=True).click()
    page.get_by_label("Mission ID", exact=True).fill("mission")
    page.get_by_label("Station name", exact=True).fill("Aurora")
    page.get_by_label("People count", exact=True).fill("10")
    page.get_by_label("Created at", exact=True).fill("0")
    page.get_by_role("button", name="Add ship", exact=True).click()
    ship = page.get_by_role("group", name="Ship 1", exact=True)
    ship.get_by_label("Ship ID", exact=True).fill("A")
    ship.get_by_label("Name", exact=True).fill("Atlas")
    page.get_by_role("button", name="Add response rule", exact=True).click()
    rule = page.get_by_role("group", name="Response rule 1", exact=True)
    rule.get_by_label("Ship ID", exact=True).fill("A")
    rule.get_by_label("Request ordinal", exact=True).fill("1")
    rule.get_by_label("Outcome", exact=True).select_option("accepted")
    result = page.evaluate("window.testEditor.value()")
    assert result["time_horizon_seconds"] == "10.5"
    assert result["baseline"]["missions"][0]["people_count"] == 10
    assert result["response_rules"][0]["confirmed_seats"] is None
    response = TestClient(create_app()).post(
        "/runs",
        json={"application_run_id": "nested", "central_id": "central", "scenarios": [result]},
    )
    assert response.status_code == 201, response.text
    mission = page.get_by_role("group", name="Mission 1", exact=True)
    mission.get_by_role("button", name="Add history entry", exact=True).click()
    history = mission.get_by_role("group", name="History entry 1", exact=True)
    for label, value in {
        "Event ID": "closed",
        "Mission sequence": "1",
        "Recorded at": "0",
        "Confirmed seats delta": "0",
        "Pending seats delta": "-2",
        "Reason": "cancelled",
    }.items():
        history.get_by_label(label, exact=True).fill(value)
    history.get_by_label("Action", exact=True).select_option("cancelled")
    signed = page.evaluate("window.testEditor.value()")
    assert signed["baseline"]["missions"][0]["history"][0]["pending_seats_delta"] == -2
    signed_response = TestClient(create_app()).post(
        "/runs",
        json={"application_run_id": "signed", "central_id": "central", "scenarios": [signed]},
    )
    assert signed_response.status_code == 201, signed_response.text
    page.get_by_role("button", name="Remove response rule 1", exact=True).click()
    assert page.evaluate("window.testEditor.value().response_rules") == []


def test_response_form_supports_sequence_envelope(page: Page, web_origin: str):
    """Submit the public response envelope with zero seats and exact decimal timing."""
    page.goto(web_origin)
    page.evaluate("""async () => {
      const { createForms, createOutcomes } = await import('/shared/ui/controls.js');
      const { registerResponses } = await import('/communication/responses/index.js');
      document.body.replaceChildren();
      const root = document.createElement('main'); document.body.append(root);
      const workspace = { invoke: async (operation, payload) => {
        window.submission = { operation, payload }; return {status:'applied',value:null};
      }};
      registerResponses({forms:createForms({root,workspace,outcomes:createOutcomes()})});
    }""")
    for label, value in {
        "Message ID": "m",
        "Delivery ID": "d",
        "Attempt number": "1",
        "Request ID": "r",
        "Confirmed seats": "0",
        "Sent at (seconds)": "1.25",
    }.items():
        page.get_by_label(label, exact=True).fill(value)
    page.get_by_label("Outcome", exact=True).select_option("refused")
    page.get_by_label("Include session envelope", exact=True).check()
    page.get_by_label("Session ID", exact=True).fill("s")
    page.get_by_label("Session version", exact=True).fill("1")
    page.get_by_label("Sequence", exact=True).fill("3")
    page.get_by_role("button", name="Record response", exact=True).click()
    expect(page.get_by_text("Record response: applied", exact=True)).to_be_visible()
    command = page.evaluate("window.submission.payload.command")
    assert command["confirmed_seats"] == 0
    assert command["received_at"] is None
    assert command["sent_at"] == "1.25"
    assert command["envelope"] == {
        "session_id": "s",
        "version": 1,
        "direction": "inbound",
        "sequence": 3,
    }
