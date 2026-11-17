/**
 * What: presents the selected run, live committed state and on-demand call history.
 * When called: the shell mounts the Exploration tab for an open run.
 * Why: users must inspect the same authoritative run while keeping costly history reads explicit.
 */
export function registerRunInspection({ root, workspace, outcomes }) {
  const section = document.createElement("section");
  section.setAttribute("aria-labelledby", "run-inspection-heading");
  const heading = document.createElement("h2");
  heading.id = "run-inspection-heading";
  heading.textContent = "Run inspection";
  const refresh = document.createElement("button");
  refresh.type = "button";
  refresh.textContent = "Refresh state";
  const historyButton = document.createElement("button");
  historyButton.type = "button";
  historyButton.textContent = "Load call history";
  const status = document.createElement("p");
  status.setAttribute("aria-live", "polite");
  const state = document.createElement("details");
  const stateSummary = document.createElement("summary");
  stateSummary.textContent = "Complete run state";
  const stateValue = document.createElement("pre");
  state.append(stateSummary, stateValue);
  const activity = document.createElement("div");
  activity.setAttribute("aria-label", "Call history");
  section.append(heading, status, refresh, historyButton, state, activity);

  refresh.addEventListener("click", async () => {
    const version = workspace.getSnapshot().selectionVersion;
    refresh.disabled = true;
    try {
      await workspace.refreshState();
    } catch {
      if (version !== workspace.getSnapshot().selectionVersion) return;
      status.textContent = "Refresh failed. Showing the last successful state as stale.";
    } finally {
      refresh.disabled = false;
    }
  });
  historyButton.addEventListener("click", async () => {
    const version = workspace.getSnapshot().selectionVersion;
    historyButton.disabled = true;
    try {
      const historyResult = await workspace.loadHistory();
      if (version === workspace.getSnapshot().selectionVersion) renderCallHistory(activity, historyResult, outcomes);
    } catch (error) {
      if (version !== workspace.getSnapshot().selectionVersion) return;
      activity.replaceChildren();
      const message = document.createElement("p");
      message.setAttribute("role", "alert");
      message.textContent = `Call history unavailable: ${error.message}`;
      activity.append(message);
    } finally {
      historyButton.disabled = false;
    }
  });

  const render = (current) => {
    status.textContent = current.stale
      ? "State is stale; the last successful snapshot is shown."
      : current.refreshedAt
        ? `Last refreshed ${current.refreshedAt}`
        : "State has not been refreshed yet.";
    stateValue.textContent = JSON.stringify(current.snapshot, null, 2);
    if (current.history !== null) renderCallHistory(activity, current.history, outcomes);
    else activity.replaceChildren();
  };
  const unsubscribe = workspace.subscribe(render);
  render(workspace.getSnapshot());
  root.append(section);
  return unsubscribe;
}

function renderCallHistory(target, result, outcomes) {
  target.replaceChildren();
  const title = document.createElement("h3");
  title.textContent = "Call history";
  target.append(title);
  const entries = Array.isArray(result) ? result : result?.value ?? [];
  if (!Array.isArray(entries) || entries.length === 0) {
    const empty = document.createElement("p");
    empty.textContent = "No call history entries.";
    target.append(empty);
    return;
  }
  entries.forEach((entry, index) => {
    const item = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = `Call ${index + 1}: ${entry.operation ?? entry.path ?? "Recorded call"} (HTTP ${entry.status_code ?? entry.status ?? "unknown"}${entry.response?.status ? ` · ${entry.response.status}` : ""}${entry.response?.reason ? ` · ${entry.response.reason}` : ""})`;
    item.append(summary);
    const body = document.createElement("pre");
    body.textContent = JSON.stringify(entry, null, 2);
    item.append(body);
    target.append(item);
  });
  if (result && !Array.isArray(result)) outcomes.render(result, { label: "History response", target: target.appendChild(document.createElement("div")) });
}
