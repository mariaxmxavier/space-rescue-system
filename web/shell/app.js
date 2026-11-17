import { createApiClient } from "../shared/api/client.js";
import { createWorkspace } from "../shared/state/workspace.js";
import { createForms, createOutcomes } from "../shared/ui/controls.js";
import { registerMissions } from "../missions/index.js";
import { registerFleet } from "../fleet/index.js";
import { registerQuotes } from "../quotes/index.js";
import { registerRequests } from "../requests/index.js";
import { registerMobilisation } from "../mobilisation/index.js";
import { registerCommunication } from "../communication/index.js";
import { registerExperiments } from "../experiments/index.js";
import { registerRunInspection } from "../exploration/run/index.js";
import { registerMissionHistory } from "../missions/history/index.js";
import { registerDecisionInspection } from "../mobilisation/decisions/index.js";
import { registerSimulationViewer } from "../simulations/index.js";

/**
 * What: composes the browser app, its shared run state and capability registration points.
 * When called: the module loads from index.html.
 * Why: one outer layer owns browser wiring while rescue policy remains in the API.
 */
export function startApp(documentRef = document) {
  const api = createApiClient();
  const manualMode = typeof location !== "undefined" && new URL(location.href).searchParams.get("workspace") === "manual";
  const viewerRoot = documentRef.querySelector("#simulation-viewer");
  const advancedWorkspace = documentRef.querySelector("#advanced-workspace");
  if (manualMode) {
    viewerRoot.hidden = true;
    advancedWorkspace.open = true;
  } else {
    registerSimulationViewer({ root: viewerRoot, api });
  }
  const workspace = createWorkspace(api);
  const outcomes = createOutcomes();
  const capabilityRoot = documentRef.querySelector("#capabilities");
  const explorationPanel = documentRef.querySelector("#exploration-panel");
  let explorationRoot = documentRef.querySelector("#exploration-capabilities");
  if (!explorationRoot) {
    explorationRoot = documentRef.createElement("div");
    explorationRoot.id = "exploration-capabilities";
    explorationRoot.className = "capability-grid";
    explorationPanel.insertBefore(explorationRoot, documentRef.querySelector("#exploration-state"));
  }
  const forms = createForms({ root: capabilityRoot, workspace, outcomes });
  const context = Object.freeze({ root: capabilityRoot, api, workspace, forms, outcomes });
  const capabilities = new Map();
  const runIdField = documentRef.querySelector("#application-run-id");
  const centralIdField = documentRef.querySelector("#central-id");
  const error = documentRef.querySelector("#workspace-error");
  documentRef.querySelector("#api-origin").textContent = api.origin;
  const capabilityButtons = documentRef.createElement("nav");
  capabilityButtons.className = "capability-navigation";
  capabilityButtons.setAttribute("aria-label", "Rescue capabilities");
  const capabilityViews = new Map();
  const capabilityHandles = new Map();
  const selectedCapabilities = { operations: "Missions", exploration: "Communication" };
  const definitions = [
    ["Missions", "operations", registerMissions], ["Fleet", "operations", registerFleet],
    ["Quotes", "operations", registerQuotes], ["Requests", "operations", registerRequests],
    ["Mobilisation", "operations", registerMobilisation], ["Communication", "exploration", registerCommunication],
    ["Experiments", "exploration", registerExperiments], ["Run inspection", "exploration", registerRunInspection],
    ["Mission history", "exploration", registerMissionHistory], ["Decisions", "exploration", registerDecisionInspection],
  ];
  capabilityRoot.replaceChildren();
  documentRef.querySelector("#manual-workspace").insertBefore(capabilityButtons, documentRef.querySelector("#operations-panel"));
  function mountCapability(name) {
    const definition = definitions.find(([label]) => label === name);
    if (!definition) return null;
    const [, tab, register] = definition;
    let view = capabilityViews.get(name);
    if (!view) {
      view = documentRef.createElement("div");
      view.className = "capability-grid";
      capabilityViews.set(name, view);
      const targetRoot = tab === "operations" ? capabilityRoot : explorationRoot;
      targetRoot.append(view);
      const capabilityForms = createForms({ root: view, workspace, outcomes });
      capabilityHandles.set(name, register({ ...context, root: view, forms: capabilityForms }));
    }
    return view;
  }
  function showCapability(name) {
    const definition = definitions.find(([label]) => label === name);
    if (!definition) return;
    const [, tab] = definition;
    selectTab(tab, false);
    selectedCapabilities[tab] = name;
    const view = mountCapability(name);
    for (const existing of capabilityViews.values()) existing.hidden = existing !== view;
    if (!view.isConnected) (tab === "operations" ? capabilityRoot : explorationRoot).append(view);
    for (const button of capabilityButtons.querySelectorAll("button")) {
      button.setAttribute("aria-current", String(button.textContent === name));
    }
  }
  for (const [label, tab] of definitions) {
    const button = documentRef.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", () => showCapability(label));
    capabilityButtons.append(button);
  }
  // Scenario configuration is part of run creation, so mount it even when the
  // operator creates a run before opening the Experiments selector.
  mountCapability("Experiments").hidden = true;
  showCapability("Missions");

  function showError(message) {
    error.textContent = message;
    error.hidden = false;
  }

  function selectTab(name, restoreCapability = true) {
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
    if (restoreCapability) showCapability(selectedCapabilities[name]);
  }

  async function openRun() {
    error.hidden = true;
    if (!runIdField.value.trim()) {
      showError("Enter a run ID to open an existing run.");
      runIdField.focus();
      return;
    }
    try {
      await workspace.selectRun(runIdField.value);
    } catch (cause) {
      showError(`Run unavailable: ${cause.message}`);
    }
  }

  documentRef.querySelector("#run-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const submit = event.currentTarget.querySelector('button[type="submit"]');
    if (submit.disabled) return;
    submit.disabled = true;
    submit.textContent = "Creating run…";
    const selectionVersion = workspace.getSnapshot().selectionVersion;
    error.hidden = true;
    try {
      const experiment = capabilityHandles.get("Experiments");
      const runConfiguration = experiment?.getRunConfiguration?.() ?? { policies: [], scenarios: [] };
      await workspace.createRun({
        application_run_id: runIdField.value,
        central_id: centralIdField.value,
        ...runConfiguration,
      });
    } catch (cause) {
      if (selectionVersion === workspace.getSnapshot().selectionVersion) {
        showError(`Could not create run: ${cause.message}`);
      }
    } finally {
      submit.disabled = false;
      submit.textContent = "Create run";
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
