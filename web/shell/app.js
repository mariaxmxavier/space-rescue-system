import { createApiClient } from "../shared/api/client.js";
import { createWorkspace } from "../shared/state/workspace.js";
import { createForms, createOutcomes } from "../shared/ui/controls.js";

/**
 * What: composes the browser app, its shared run state and capability registration points.
 * When called: the module loads from index.html.
 * Why: one outer layer owns browser wiring while rescue policy remains in the API.
 */
export function startApp(documentRef = document) {
  const api = createApiClient();
  const workspace = createWorkspace(api);
  const outcomes = createOutcomes();
  const capabilityRoot = documentRef.querySelector("#capabilities");
  const forms = createForms({ root: capabilityRoot, workspace, outcomes });
  const context = Object.freeze({ root: capabilityRoot, api, workspace, forms, outcomes });
  const capabilities = new Map();
  const runIdField = documentRef.querySelector("#application-run-id");
  const centralIdField = documentRef.querySelector("#central-id");
  const error = documentRef.querySelector("#workspace-error");

  function showError(message) {
    error.textContent = message;
    error.hidden = false;
  }

  function selectTab(name) {
    error.hidden = true;
    const operations = name === "operations";
    const operationsTab = documentRef.querySelector("#operations-tab");
    const explorationTab = documentRef.querySelector("#exploration-tab");
    operationsTab.setAttribute("aria-selected", String(operations));
    explorationTab.setAttribute("aria-selected", String(!operations));
    operationsTab.tabIndex = operations ? 0 : -1;
    explorationTab.tabIndex = operations ? -1 : 0;
    documentRef.querySelector("#operations-panel").hidden = !operations;
    documentRef.querySelector("#exploration-panel").hidden = operations;
  }

  async function openRun() {
    error.hidden = true;
    try {
      await workspace.selectRun(runIdField.value);
    } catch (cause) {
      showError(`Run unavailable: ${cause.message}`);
    }
  }

  documentRef.querySelector("#run-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    error.hidden = true;
    try {
      await workspace.createRun({
        application_run_id: runIdField.value,
        central_id: centralIdField.value,
        policies: [],
        scenarios: [],
      });
    } catch (cause) {
      showError(`Could not create run: ${cause.message}`);
    }
  });
  documentRef.querySelector("#open-run").addEventListener("click", openRun);
  documentRef.querySelector("#operations-tab").addEventListener("click", () => selectTab("operations"));
  documentRef.querySelector("#exploration-tab").addEventListener("click", () => selectTab("exploration"));
  for (const tab of ["operations-tab", "exploration-tab"]) {
    documentRef.querySelector(`#${tab}`).addEventListener("keydown", (event) => {
      if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
        event.preventDefault();
        const next = tab === "operations-tab" ? "exploration-tab" : "operations-tab";
        documentRef.querySelector(`#${next}`).focus();
        documentRef.querySelector(`#${next}`).click();
      }
    });
  }

  for (const buttonId of ["refresh-operations", "refresh-exploration"]) {
    documentRef.querySelector(`#${buttonId}`).addEventListener("click", async () => {
      try { await workspace.refreshState(); } catch (cause) { showError(cause.message); }
    });
  }
  documentRef.querySelector("#load-history").addEventListener("click", async () => {
    selectTab("exploration");
    try { await workspace.loadHistory(); } catch (cause) { showError(cause.message); }
  });

  documentRef.querySelector("#mission-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    error.hidden = true;
    const form = event.currentTarget;
    const button = form.querySelector("button");
    const result = form.querySelector(".form-result");
    button.disabled = true;
    button.textContent = "Submitting…";
    try {
      const response = await workspace.invoke("register_mission", { command: {
        mission_id: form.elements.mission_id.value,
        station_name: form.elements.station_name.value,
        people_count: Number(form.elements.people_count.value),
        created_at: form.elements.created_at.value,
      } });
      outcomes.render(response, { label: "Register mission", target: result });
    } catch (cause) {
      result.replaceChildren();
      const message = documentRef.createElement("p");
      message.setAttribute("role", "alert");
      message.textContent = cause.message;
      result.append(message);
    } finally {
      button.disabled = false;
      button.textContent = "Register mission";
    }
  });

  workspace.subscribe((state) => renderWorkspace(documentRef, state));
  const priorRun = globalThis.localStorage?.getItem("space-rescue-run-id");
  if (priorRun) {
    runIdField.value = priorRun;
    void openRun();
  }

  return Object.freeze({
    api,
    workspace,
    forms,
    outcomes,
    registerCapability(name, register) {
      if (capabilities.has(name)) throw new Error(`Capability already registered: ${name}`);
      capabilities.set(name, register(context));
    },
    getCapabilityContext: () => context,
  });
}

/** What: maps one immutable workspace snapshot to accessible summaries. When: run state changes. Why: both tabs stay consistent. */
function renderWorkspace(documentRef, state) {
  documentRef.querySelector("#selected-run").textContent = state.runId || "No run selected";
  const refreshStatus = documentRef.querySelector("#refresh-status");
  refreshStatus.textContent = state.stale ? "Connection issue · showing last saved view (stale)" : state.refreshedAt ? `Updated ${new Date(state.refreshedAt).toLocaleTimeString()}` : state.runId ? "Loading current state" : "Waiting for a run";
  const summary = documentRef.querySelector("#mission-summary");
  const missions = state.snapshot?.missions || [];
  summary.replaceChildren(...missions.map((mission) => {
    const card = documentRef.createElement("article");
    card.className = "summary-card";
    card.innerHTML = `<span>Mission</span><strong></strong><span>Demand: ${escapeHtml(mission.data?.people_count ?? mission.people_count ?? "—")}</span>`;
    card.querySelector("strong").textContent = mission.mission_id || mission.data?.mission_id || "Unidentified mission";
    return card;
  }));
  const stateView = documentRef.querySelector("#exploration-state");
  stateView.replaceChildren();
  if (state.snapshot) {
    const details = documentRef.createElement("details");
    const title = documentRef.createElement("summary");
    title.textContent = "Complete committed state";
    const pre = documentRef.createElement("pre");
    pre.textContent = JSON.stringify(state.snapshot, null, 2);
    details.append(title, pre);
    stateView.append(details);
  }
  const history = documentRef.querySelector("#history-content");
  history.replaceChildren();
  if (state.history !== null) {
    const pre = documentRef.createElement("pre");
    pre.textContent = JSON.stringify(state.history, null, 2);
    history.append(pre);
  }
}

/** What: HTML-escapes server-derived quantities in a summary card. When: the mission summary renders. Why: values cannot become markup. */
function escapeHtml(value) { return String(value).replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[ch]); }

if (typeof document !== "undefined") startApp();
